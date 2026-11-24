import asyncio
from fastmcp import Client, FastMCP
from src.tools.system_tools import register_system_tools  # ปรับ path ให้ตรงกับตำแหน่งไฟล์ของคุณ (เช่น src.system_tool)


def _create_test_mcp() -> FastMCP:
    mcp = FastMCP("test-gateway")
    register_system_tools(mcp)
    return mcp


def test_ping_server():
    async def _run():
        mcp = _create_test_mcp()
        async with Client(mcp) as client:
            result = await client.call_tool("ping_server", {})
            assert "Pong!" in str(result)

    asyncio.run(_run())


def test_get_host_info():
    async def _run():
        mcp = _create_test_mcp()
        async with Client(mcp) as client:
            result = await client.call_tool("get_host_info", {})
            assert "python_version" in str(result)

    asyncio.run(_run())