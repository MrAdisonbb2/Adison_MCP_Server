import datetime
import platform
from fastmcp import FastMCP
from mcp.types import ToolAnnotations


def register_system_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )
    )
    def ping_server() -> str:
        """ใช้ทดสอบการเชื่อมต่อว่า Adison MCP Server ทำงานปกติหรือไม่"""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"Pong! Adison MCP Server is online. Server time: {now}"

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )
    )
    def get_host_info() -> dict:
        """ดึงข้อมูลพื้นฐานของระบบปฏิบัติการและสภาพแวดล้อมที่รัน MCP Server อยู่"""
        return {
            "node": platform.node(),
            "os": platform.system(),
            "release": platform.release(),
            "python_version": platform.python_version(),
        }