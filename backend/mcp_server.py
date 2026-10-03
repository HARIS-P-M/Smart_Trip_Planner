"""MCP server exposing travel tools over stdio. Run standalone: python mcp_server.py"""
from mcp.server.fastmcp import FastMCP
import tools

mcp = FastMCP("travel-tools")
for fn in (tools.search_flights, tools.search_hotels, tools.convert_currency, tools.get_weather):
    mcp.tool()(fn)

if __name__ == "__main__":
    mcp.run()
