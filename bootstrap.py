"""
Bootstrap file to initialize and run the MCP server.
"""
from mcp_server import MCPServer

def main():
    server = MCPServer()
    server.run()

if __name__ == "__main__":
    main()
