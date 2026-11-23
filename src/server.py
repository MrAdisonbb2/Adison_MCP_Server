import os
from dotenv import load_dotenv
from fastmcp import FastMCP

from src.proxy_manager import load_external_mcps
from src.tools.system_tools import register_system_tools
from src.web.routes import register_web_routes

load_dotenv()

mcp = FastMCP("Adison-Central-MCP")

# 1. โหลดเครื่องมือเช็กสถานะพื้นฐาน
register_system_tools(mcp)

# 2. โหลด MCP ภายนอกทั้งหมดจากไฟล์ mcp_servers.json อัตโนมัติ
load_external_mcps(mcp)

# 3. ลงทะเบียนหน้าเว็บ Dashboard (/admin) และ CRUD API (/api/servers)
register_web_routes(mcp)

if __name__ == "__main__":
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))

    print(f"Starting Adison MCP Gateway on http://{host}:{port}/mcp")
    print(f"Admin Web Dashboard available at http://localhost:{port}/admin")
    mcp.run(transport="http", host=host, port=port)