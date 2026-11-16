# Adison Central MCP Server

Centralized Model Context Protocol (MCP) server built with **FastMCP**, exposing system diagnostics and Notion workspace tools over SSE (`http://<host>:8000/sse`).

## Available Tools

### System Tools (`src/tools/system_tools.py`)
- `ping_server`: Check server availability and current server timestamp.
- `get_host_info`: Retrieve host OS, release, node name, and Python version.

### API & Notion Tools (`src/tools/api_tools.py`)
- `fetch_json_from_url`: Perform HTTP GET requests to public JSON REST APIs.
- `search_notion`: Search Notion pages by keyword and return Page IDs and URLs.
- `read_notion_page`: Read text blocks from a specific Notion page.
- `create_notion_page`: Create a new sub-page inside a parent Notion page.

---

## Setup & Deployment

### 1. Configure Environment
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env