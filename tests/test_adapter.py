"""Offline tests: simulated MCP transport, no Editor or network."""
import io
import json
import sys
import unittest
from unittest import mock
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lib_unreal.client import UnrealMCP, MCPError, validate_endpoint


class MCPClientTests(unittest.TestCase):
    def test_local_endpoint_only(self):
        self.assertEqual(validate_endpoint("http://127.0.0.1:8000/mcp"),
                         "http://127.0.0.1:8000/mcp")
        for address in ("https://example.com/mcp", "http://192.168.1.2:8000/mcp",
                        "http://localhost/mcp", "http://x@localhost:8000/mcp",
                        "file:///etc/passwd", "http://localhost:8000/mcp?redirect=1",
                        "http://localhost:0/mcp"):
            with self.subTest(address=address), self.assertRaises(ValueError):
                validate_endpoint(address)

    def test_initialize_notification_and_tool_discovery(self):
        seen = []
        def fake(message):
            seen.append(message)
            if message["method"] == "initialize":
                return {"jsonrpc": "2.0", "id": message["id"],
                        "result": {"protocolVersion": "2025-06-18",
                                   "serverInfo": {"name": "fake"}}}
            if message["method"] == "notifications/initialized":
                return {}
            if message["method"] == "tools/list":
                return {"jsonrpc": "2.0", "id": message["id"],
                        "result": {"tools": [{"name": "list_toolsets"}]}}
            raise AssertionError(message)
        client = UnrealMCP(transport=fake)
        self.assertEqual(client.connect()["serverInfo"]["name"], "fake")
        self.assertEqual([x["name"] for x in client.list_tools()], ["list_toolsets"])
        self.assertEqual([x["method"] for x in seen],
                         ["initialize", "notifications/initialized", "tools/list"])

    def test_pagination(self):
        def fake(message):
            cursor = message.get("params", {}).get("cursor")
            return {"jsonrpc": "2.0", "id": message["id"],
                    "result": {"tools": [{"name": cursor or "first"}],
                               **({"nextCursor": "next"} if not cursor else {})}}
        self.assertEqual(len(UnrealMCP(transport=fake).list_tools()), 2)

    def test_replayed_request_id_rejected(self):
        client = UnrealMCP(transport=lambda _: {
            "jsonrpc": "2.0", "id": 999, "result": {"tools": []}})
        with self.assertRaises(MCPError):
            client.list_tools()

    def test_remote_error_rejected(self):
        client = UnrealMCP(transport=lambda msg: {
            "jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32000}})
        with self.assertRaises(MCPError):
            client.list_tools()

    def test_sse_ignores_heartbeat_and_other_request_id(self):
        events = (b": ping\\n\\n"
                  b"data: {\\"jsonrpc\\":\\"2.0\\",\\"id\\":88,\\"result\\":{}}\\n\\n"
                  b"event: message\\n"
                  b"data: {\\"jsonrpc\\":\\"2.0\\",\\"id\\":1,\\"result\\":{\\"tools\\":[]}}\\n\\n")
        response = io.BytesIO(events)
        self.assertEqual(UnrealMCP._read_sse(response, 1)["id"], 1)

    def test_sse_rejects_incomplete_or_oversized_events(self):
        with self.assertRaises(MCPError):
            UnrealMCP._read_sse(io.BytesIO(b": keepalive\\n\\n"), 1)
        with self.assertRaises(MCPError):
            UnrealMCP._read_sse(io.BytesIO(b"data: " + b"x" * (1024 * 1024 + 1)), 1)

    def test_http_disables_proxies_and_tracks_session(self):
        class FakeResponse(io.BytesIO):
            def __init__(self, payload):
                super().__init__(payload)
                self.status = 200
                self.headers = {"Content-Type": "application/json",
                                "Mcp-Session-Id": "test-session"}
        response = FakeResponse(json.dumps(
            {"jsonrpc": "2.0", "id": 1, "result": {"tools": []}}).encode())
        with mock.patch("lib_unreal.client.request.build_opener") as builder:
            builder.return_value.open.return_value = response
            client = UnrealMCP()
            reply = client._post({"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/list"})
            self.assertEqual(reply["result"]["tools"], [])
            self.assertEqual(client._session_id, "test-session")
            args = builder.call_args.args
            self.assertTrue(any(isinstance(x, mock.Mock) is False and
                                isinstance(x, __import__("urllib").request.ProxyHandler)
                                and x.proxies == {} for x in args))

    def test_http_rejects_accepted_request_without_result(self):
        class Accepted(io.BytesIO):
            status = 202
            headers = {"Content-Type": "application/json"}
        with mock.patch("lib_unreal.client.request.build_opener") as builder:
            builder.return_value.open.return_value = Accepted(b"")
            with self.assertRaises(MCPError):
                UnrealMCP()._post({"jsonrpc": "2.0", "id": 1,
                                    "method": "tools/list"})

    def test_invalid_timeout(self):
        with self.assertRaises(ValueError):
            UnrealMCP(timeout=0)


if __name__ == "__main__":
    unittest.main()
