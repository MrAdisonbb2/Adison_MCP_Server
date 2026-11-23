import json
import os
import re
import shutil
from pathlib import Path
from typing import Any
from fastmcp import FastMCP

CONFIG_PATH = Path("mcp_servers.json")
BACKUP_PATH = Path("mcp_servers.json.bak")

# เก็บรายชื่อ Prefix ของ Proxy ที่ถูก Mount อยู่ในปัจจุบัน เพื่อใช้ถอดออกตอน Reload
_mounted_prefixes: list[str] = []


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
    """ถอด Proxy เก่าทั้งหมดออกจาก FastMCP ก่อนทำการ Reload"""
    global _mounted_prefixes
    if not _mounted_prefixes:
        return

    # รองรับโครงสร้าง Mount ของ FastMCP (ลบออกจากรายการ mounted servers)
    if hasattr(mcp, "_mounted_servers") and isinstance(mcp._mounted_servers, dict):
        for prefix in _mounted_prefixes:
            mcp._mounted_servers.pop(prefix, None)
    elif hasattr(mcp, "mounted_servers") and isinstance(mcp.mounted_servers, list):
        mcp.mounted_servers[:] = [
            m for m in mcp.mounted_servers if getattr(m, "prefix", None) not in _mounted_prefixes
        ]

    _mounted_prefixes.clear()


def load_external_mcps(mcp: FastMCP) -> dict[str, Any]:
    """โหลดและ Mount MCP ภายนอกทั้งหมดจาก mcp_servers.json เข้าสู่ FastMCP"""
    global _mounted_prefixes
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
            proxy = FastMCP.as_proxy({"mcpServers": {name: server_cfg}}, name=name)
            mcp.mount(proxy, prefix=name)
            _mounted_prefixes.append(name)
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