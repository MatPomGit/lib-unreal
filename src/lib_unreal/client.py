"""Read-only MCP client for the Unreal Editor's loopback server."""
import json
from urllib import request, error
from urllib.parse import urlsplit

DEFAULT_ENDPOINT = "http://127.0.0.1:8000/mcp"
PROTOCOL_VERSION = "2025-06-18"
MAX_RESPONSE = 1024 * 1024


class MCPError(RuntimeError):
    """A protocol, transport or remote MCP error."""


def validate_endpoint(endpoint):
    parsed = urlsplit(endpoint)
    if (parsed.scheme != "http" or parsed.hostname not in
            {"127.0.0.1", "localhost", "::1"} or parsed.username or
            parsed.password or parsed.fragment or parsed.query or
            not parsed.path.startswith("/")):
        raise ValueError("MCP endpoint must be HTTP on loopback without credentials")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Invalid MCP port") from exc
    if port is None or port < 1:
        raise ValueError("Valid explicit MCP port required")
    return endpoint


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise MCPError("MCP redirects are not allowed")


class UnrealMCP:
    """Discover tools only. No tools/call entrypoint exists in this library."""

    def __init__(self, endpoint=DEFAULT_ENDPOINT, timeout=10, transport=None):
        self.endpoint = validate_endpoint(endpoint)
        if timeout <= 0 or timeout > 60:
            raise ValueError("timeout must be in (0, 60] seconds")
        self.timeout = timeout
        self.transport = transport or self._post
        self._sequence = 0
        self._session_id = None

    @staticmethod
    def _read_sse(response, expected_id):
        """Read complete SSE events; ignore comments and unrelated JSON-RPC ids."""
        used = 0
        fields = []
        while True:
            line = response.readline(MAX_RESPONSE - used + 1)
            used += len(line)
            if used > MAX_RESPONSE:
                raise MCPError("MCP SSE response exceeds byte limit")
            if not line:
                break
            if line in (b"\\n", b"\\r\\n"):
                if fields:
                    try:
                        event = json.loads(b"\\n".join(fields))
                    except (ValueError, UnicodeError) as exc:
                        raise MCPError("Malformed MCP SSE event JSON") from exc
                    if isinstance(event, dict) and event.get("id") == expected_id:
                        return event
                    fields = []
            elif line.startswith(b"data:"):
                fields.append(line[5:].strip())
        raise MCPError("MCP SSE stream ended without the requested response")

    def _post(self, message):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": PROTOCOL_VERSION,
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        payload = json.dumps(message, separators=(",", ":")).encode("utf-8")
        req = request.Request(self.endpoint, payload, headers, method="POST")
        # Do not trust HTTP(S)_PROXY or NO_PROXY for loopback MCP requests.
        opener = request.build_opener(request.ProxyHandler({}), _NoRedirect())
        try:
            with opener.open(req, timeout=self.timeout) as response:
                session = response.headers.get("Mcp-Session-Id")
                if session:
                    self._session_id = session
                if response.status == 202:
                    if "id" in message:
                        raise MCPError("MCP request unexpectedly returned 202")
                    return {}
                content_type = response.headers.get("Content-Type", "")
                if "text/event-stream" in content_type:
                    return self._read_sse(response, message.get("id"))
                if "application/json" not in content_type:
                    raise MCPError("Unexpected MCP response content type")
                raw = response.read(MAX_RESPONSE + 1)
                if len(raw) > MAX_RESPONSE:
                    raise MCPError("MCP response exceeds byte limit")
                try:
                    return json.loads(raw)
                except (ValueError, UnicodeError) as exc:
                    raise MCPError("Malformed MCP JSON response") from exc
        except OSError as exc:
            raise MCPError(f"MCP transport failed: {exc}") from exc

    def _rpc(self, method, params=None):
        self._sequence += 1
        msg = {"jsonrpc": "2.0", "id": self._sequence, "method": method}
        if params is not None:
            msg["params"] = params
        reply = self.transport(msg)
        if not isinstance(reply, dict) or reply.get("jsonrpc") != "2.0":
            raise MCPError("Malformed MCP JSON-RPC response")
        if reply.get("id") != self._sequence:
            raise MCPError("MCP response id does not match request")
        if reply.get("error") is not None:
            raise MCPError(f"MCP remote error: {reply['error']}")
        if "result" not in reply:
            raise MCPError("MCP JSON-RPC result missing")
        return reply["result"]

    def connect(self):
        result = self._rpc("initialize", {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "lib-unreal", "version": "0.1.0"},
        })
        if not isinstance(result, dict) or not result.get("protocolVersion"):
            raise MCPError("Invalid MCP initialization result")
        self.transport({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return result

    def list_tools(self):
        tools = []
        cursor = None
        seen = set()
        while True:
            params = {"cursor": cursor} if cursor else {}
            result = self._rpc("tools/list", params)
            if not isinstance(result, dict) or not isinstance(result.get("tools"), list):
                raise MCPError("Invalid MCP tools/list result")
            tools.extend(result["tools"])
            cursor = result.get("nextCursor")
            if not cursor:
                return tools
            if not isinstance(cursor, str) or cursor in seen:
                raise MCPError("Invalid or repeated MCP pagination cursor")
            seen.add(cursor)
