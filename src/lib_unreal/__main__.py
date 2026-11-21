"""Local, read-only Unreal MCP tool discovery."""
import argparse
import json
from .client import DEFAULT_ENDPOINT, UnrealMCP


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    args = parser.parse_args(argv)
    client = UnrealMCP(endpoint=args.endpoint)
    server = client.connect()
    tools = client.list_tools()
    print(json.dumps({"server": server.get("serverInfo", {}),
                      "protocolVersion": server["protocolVersion"],
                      "tools": tools}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
