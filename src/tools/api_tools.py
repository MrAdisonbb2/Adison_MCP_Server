import os
import httpx
from fastmcp import FastMCP

NOTION_BASE_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _get_notion_headers() -> dict | None:
    api_key = os.getenv("NOTION_API_KEY")
    if not api_key or api_key == "your_notion_integration_token_here":
        return None
    return {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def register_api_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def fetch_json_from_url(url: str) -> dict | str:
        """ดึงข้อมูล JSON จาก REST API สาธารณะภายนอกผ่าน HTTP GET"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                return f"HTTP Error: {str(e)}"

    @mcp.tool()
    async def search_notion(query: str) -> list[dict] | str:
        """ค้นหาหน้า (Pages) ใน Notion Workspace จากคำค้นหา และคืนค่าเป็น Title พร้อม Page ID"""
        headers = _get_notion_headers()
        if not headers:
            return "Error: ยังไม่ได้ตั้งค่า NOTION_API_KEY ในไฟล์ .env"

        payload = {"query": query, "page_size": 10}
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.post(f"{NOTION_BASE_URL}/search", headers=headers, json=payload)
                res.raise_for_status()
                results = res.json().get("results", [])

                pages = []
                for item in results:
                    if item.get("object") != "page":
                        continue
                    title = "Untitled"
                    for prop in item.get("properties", {}).values():
                        if prop.get("type") == "title" and prop.get("title"):
                            title = "".join(t.get("plain_text", "") for t in prop["title"])
                            break
                    pages.append({
                        "page_id": item.get("id"),
                        "title": title,
                        "url": item.get("url"),
                    })
                return pages if pages else "ไม่พบหน้าที่ตรงกับคำค้นหา"
            except httpx.HTTPError as e:
                return f"Notion Search Error: {str(e)}"

    @mcp.tool()
    async def read_notion_page(page_id: str) -> str:
        """อ่านเนื้อหาข้อความภายในหน้า Notion จาก page_id ที่ได้จากการค้นหา"""
        headers = _get_notion_headers()
        if not headers:
            return "Error: ยังไม่ได้ตั้งค่า NOTION_API_KEY ในไฟล์ .env"

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.get(
                    f"{NOTION_BASE_URL}/blocks/{page_id}/children",
                    headers=headers,
                    params={"page_size": 50},
                )
                res.raise_for_status()
                blocks = res.json().get("results", [])

                lines = []
                for block in blocks:
                    b_type = block.get("type")
                    rich_texts = block.get(b_type, {}).get("rich_text", [])
                    text = "".join(rt.get("plain_text", "") for rt in rich_texts)
                    if text:
                        lines.append(text)
                return "\n".join(lines) if lines else "(หน้านี้ยังไม่มีเนื้อหาข้อความ)"
            except httpx.HTTPError as e:
                return f"Notion Read Error: {str(e)}"

    @mcp.tool()
    async def create_notion_page(parent_page_id: str, title: str, content: str) -> str:
        """สร้างหน้าย่อยใหม่ใน Notion ภายใต้ parent_page_id พร้อมใส่หัวข้อและเนื้อหาเริ่มต้น"""
        headers = _get_notion_headers()
        if not headers:
            return "Error: ยังไม่ได้ตั้งค่า NOTION_API_KEY ในไฟล์ .env"

        payload = {
            "parent": {"page_id": parent_page_id},
            "properties": {
                "title": {
                    "title": [{"text": {"content": title}}]
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content}}]
                    },
                }
            ],
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.post(f"{NOTION_BASE_URL}/pages", headers=headers, json=payload)
                res.raise_for_status()
                new_url = res.json().get("url")
                return f"สร้างหน้า Notion สำเร็จ: {new_url}"
            except httpx.HTTPError as e:
                return f"Notion Create Error: {str(e)}"