import json
from pathlib import Path
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

from src.proxy_manager import (
    delete_server,
    get_all_servers,
    load_external_mcps,
    toggle_server,
    upsert_server,
)

HTML_PATH = Path(__file__).parent / "index.html"


def register_web_routes(mcp: FastMCP) -> None:
    """ลงทะเบียน Route สำหรับหน้าเว็บ Dashboard และ CRUD API บน Port 8000"""
    
    @mcp.custom_route("/", methods=["GET"])
    async def root_redirect(request: Request) -> RedirectResponse:
        return RedirectResponse(url="/admin")

    @mcp.custom_route("/admin", methods=["GET"])
    async def admin_page(request: Request) -> HTMLResponse:
        if not HTML_PATH.exists():
            return HTMLResponse(
                "<h1>ไม่พบไฟล์ src/web/index.html</h1>",
                status_code=404,
            )
        return HTMLResponse(HTML_PATH.read_text(encoding="utf-8"))

    @mcp.custom_route("/api/servers", methods=["GET"])
    async def api_list_servers(request: Request) -> JSONResponse:
        try:
            servers = get_all_servers()
            return JSONResponse({"status": "ok", "servers": servers})
        except Exception as e:
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    @mcp.custom_route("/api/servers", methods=["POST"])
    async def api_upsert_server(request: Request) -> JSONResponse:
        """เพิ่มหรือแก้ไข MCP Server รองรับทั้งแบบแยกชื่อ+Config และแบบวางก้อน JSON เต็ม"""
        try:
            body = await request.json()
            name = str(body.get("name", "")).strip()
            raw_config = body.get("config")

            # แปลงข้อความ JSON เป็น Dict กรณีส่งมาเป็น String จากกล่องข้อความบนหน้าเว็บ
            if isinstance(raw_config, str):
                raw_config = json.loads(raw_config)

            if not isinstance(raw_config, dict):
                return JSONResponse(
                    {"status": "error", "message": "รูปแบบ Config ต้องเป็น JSON Object"},
                    status_code=400,
                )

            # รองรับกรณีผู้ใช้ก๊อปปี้ทั้งบล็อก {"mcpServers": {"github": {...}}} มาวาง
            if "mcpServers" in raw_config and isinstance(raw_config["mcpServers"], dict):
                inner = raw_config["mcpServers"]
                if not name and len(inner) == 1:
                    name = next(iter(inner.keys()))
                    raw_config = inner[name]
                elif name in inner:
                    raw_config = inner[name]

            # รองรับกรณีผู้ใช้ก๊อปปี้ {"github": {"command": ...}} มาวางโดยไม่กรอกช่องชื่อแยก
            if (
                not name
                and len(raw_config) == 1
                and "command" not in raw_config
                and "url" not in raw_config
            ):
                only_key = next(iter(raw_config.keys()))
                if isinstance(raw_config[only_key], dict):
                    name = only_key
                    raw_config = raw_config[only_key]

            result = upsert_server(mcp, name, raw_config)
            return JSONResponse(
                {
                    "status": "ok",
                    "name": name,
                    "servers": get_all_servers(),
                    "reload": result,
                }
            )
        except json.JSONDecodeError as e:
            return JSONResponse(
                {"status": "error", "message": f"JSON ไม่ถูกต้อง: {e}"},
                status_code=400,
            )
        except ValueError as e:
            return JSONResponse({"status": "error", "message": str(e)}, status_code=400)
        except Exception as e:
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    @mcp.custom_route("/api/servers/{name}", methods=["DELETE"])
    async def api_delete_server(request: Request) -> JSONResponse:
        name = request.path_params.get("name", "")
        try:
            result = delete_server(mcp, name)
            return JSONResponse(
                {
                    "status": "ok",
                    "servers": get_all_servers(),
                    "reload": result,
                }
            )
        except KeyError as e:
            return JSONResponse({"status": "error", "message": str(e)}, status_code=404)
        except Exception as e:
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    @mcp.custom_route("/api/servers/{name}/toggle", methods=["POST"])
    async def api_toggle_server(request: Request) -> JSONResponse:
        name = request.path_params.get("name", "")
        try:
            result = toggle_server(mcp, name)
            return JSONResponse(
                {
                    "status": "ok",
                    "servers": get_all_servers(),
                    "reload": result,
                }
            )
        except KeyError as e:
            return JSONResponse({"status": "error", "message": str(e)}, status_code=404)
        except Exception as e:
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    @mcp.custom_route("/api/reload", methods=["POST"])
    async def api_reload_all(request: Request) -> JSONResponse:
        try:
            result = load_external_mcps(mcp)
            return JSONResponse(
                {
                    "status": "ok",
                    "servers": get_all_servers(),
                    "reload": result,
                }
            )
        except Exception as e:
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)