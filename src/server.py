import os
from dotenv import load_dotenv
from fastmcp import FastMCP

from src.tools.system_tools import register_system_tools
from src.tools.api_tools import register_api_tools

load_dotenv()

mcp = FastMCP("Adison-Central-MCP")

register_system_tools(mcp)
register_api_tools(mcp)

if __name__ == "__main__":
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))

    print(f"Starting Adison MCP Server on http://{host}:{port}/sse")
    mcp.run(transport="sse", host=host, port=port)