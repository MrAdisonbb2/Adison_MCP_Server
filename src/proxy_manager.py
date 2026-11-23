import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.server.providers.proxy import ProxyClient, ProxyProvider

CONFIG_PATH = Path("mcp_servers.json")
BACKUP_PATH = Path("mcp_servers.json.bak")

# เก็บรายการ Provider ตั้งต้นของระบบ (เช่น local_provider) เพื่อไม่ให้ถูกลบตอน Reload
_base_providers: list[Any] | None = None


def _resolve_env_vars(obj: Any) -> Any:
    """แทนที่ค่า ${VAR_NAME} ใน JSON ด้วยค่าจริงจากไฟล์ .env"""
    if isinstance(obj, str):
        return re.sub(
            r"\$\{([^}]+)\}",
            lambda m: os.getenv(m.group(1), m.group(0)),
            obj,
        )
    if isinstance(obj, list):
        return [_resolve_env_vars(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _resolve_env_vars(v) for k, v in obj.items()}
    return obj


def _read_raw_config() -> dict[str, Any]:
    """อ่านข้อมูลดิบจาก mcp_servers.json (ไม่แทนที่ตัวแปร .env)"""
    if not CONFIG_PATH.exists():
        return {"mcpServers": {}}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "mcpServers" not in data:
            return {"mcpServers": {}}
        return data
    except Exception as e:
        raise ValueError(f"รูปแบบไฟล์ {CONFIG_PATH} ไม่ถูกต้อง: {e}")


def _write_raw_config(data: dict[str, Any]) -> None:
    """สำรองไฟล์เดิมเป็น .bak แล้วเขียนข้อมูลใหม่ลง mcp_servers.json"""
    if CONFIG_PATH.exists():
        shutil.copy2(CONFIG_PATH, BACKUP_PATH)
    CONFIG_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _unmount_all(mcp: FastMCP) -> None:
    """ถอด Proxy Provider เก่าทั้งหมดออกจาก FastMCP ก่อนทำการ Reload"""
    global _base_providers
    if not hasattr(mcp, "providers") or not isinstance(mcp.providers, list):
        return

    if _base_providers is None:
        _base_providers = list(mcp.providers)
        return

    mcp.providers[:] = [p for p in mcp.providers if p in _base_providers]


def load_external_mcps(mcp: FastMCP) -> dict[str, Any]:
    """โหลดและเชื่อมต่อ MCP ภายนอกทั้งหมดจาก mcp_servers.json เข้าสู่ FastMCP 4.x"""
    _unmount_all(mcp)

    if not CONFIG_PATH.exists():
        print(f"[ProxyManager] ไม่พบไฟล์ {CONFIG_PATH} ข้ามการโหลด MCP ภายนอก")
        return {"loaded": [], "failed": {}}

    try:
        raw_data = _read_raw_config()
        resolved_data = _resolve_env_vars(raw_data)
        servers = resolved_data.get("mcpServers", {})
    except Exception as e:
        print(f"[ProxyManager] โหลด Config ล้มเหลว: {e}")
        return {"loaded": [], "failed": {"_config": str(e)}}

    loaded: list[str] = []
    failed: dict[str, str] = {}

    for name, server_cfg in servers.items():
        if server_cfg.get("disabled", False):
            continue
        try:
            mcp_config = {"mcpServers": {name: server_cfg}}
            provider = ProxyProvider(
                client_factory=lambda cfg=mcp_config: ProxyClient(cfg)
            )
            mcp.add_provider(provider, namespace=name)
            loaded.append(name)
            print(f"[ProxyManager] เชื่อมต่อ MCP '{name}' สำเร็จ")
        except Exception as e:
            failed[name] = str(e)
            print(f"[ProxyManager] เชื่อมต่อ MCP '{name}' ล้มเหลว: {e}")

    return {"loaded": loaded, "failed": failed}


# ฟังก์ชัน CRUD สำหรับเรียกใช้จาก Web API

def get_all_servers() -> dict[str, Any]:
    """ดึงรายการ MCP ทั้งหมดในรูปแบบดิบ (เพื่อแสดงผลและแก้ไขบนหน้าเว็บ)"""
    data = _read_raw_config()
    return data.get("mcpServers", {})


def upsert_server(mcp: FastMCP, name: str, config: dict[str, Any]) -> dict[str, Any]:
    """เพิ่มหรือแก้ไข MCP Server (Create / Update) แล้วสั่ง Reload ทันที"""
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("กรุณาระบุชื่อ MCP Server")
    if not isinstance(config, dict) or ("command" not in config and "url" not in config):
        raise ValueError("Config ต้องเป็น JSON Object และมี 'command' หรือ 'url'")

    data = _read_raw_config()
    data["mcpServers"][clean_name] = config
    _write_raw_config(data)
    return load_external_mcps(mcp)


def delete_server(mcp: FastMCP, name: str) -> dict[str, Any]:
    """ลบ MCP Server ออกจากไฟล์ Config (Delete) แล้วสั่ง Reload ทันที"""
    data = _read_raw_config()
    if name not in data["mcpServers"]:
        raise KeyError(f"ไม่พบ MCP ชื่อ '{name}'")

    del data["mcpServers"][name]
    _write_raw_config(data)
    return load_external_mcps(mcp)


def toggle_server(mcp: FastMCP, name: str) -> dict[str, Any]:
    """สลับสถานะเปิด/ปิด (disabled: true/false) แล้วสั่ง Reload ทันที"""
    data = _read_raw_config()
    if name not in data["mcpServers"]:
        raise KeyError(f"ไม่พบ MCP ชื่อ '{name}'")

    current_disabled = bool(data["mcpServers"][name].get("disabled", False))
    data["mcpServers"][name]["disabled"] = not current_disabled
    _write_raw_config(data)
    return load_external_mcps(mcp)