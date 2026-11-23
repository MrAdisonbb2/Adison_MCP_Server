# Adison MCP Gateway

ศูนย์กลางจัดการและรวบรวม **Model Context Protocol (MCP) Servers** แบบครบวงจร (Centralized MCP Gateway) พร้อมหน้าเว็บ Dashboard สำหรับจัดการเพิ่ม แก้ไข เปิด-ปิด และลบ MCP Servers ได้แบบ Real-time โดยไม่ต้องเขียนโค้ดหรือแก้ไขไฟล์ตั้งค่าหลายที่

---

## 1. โปรเจกต์นี้เกี่ยวกับอะไร และแก้ไขปัญหาอะไร?

### ปัญหาที่พบในการใช้งาน MCP แบบเดิม
* **ตั้งค่าซ้ำซ้อนหลายแอป:** หากใช้งาน AI Agent หลายตัวพร้อมกัน (เช่น Google Antigravity, Cursor, Windsurf, Cline, Claude Desktop) เมื่อต้องการเพิ่ม MCP ตัวใหม่ ต้องตามไปก๊อปปี้วาง Config ในทุกแอป
* **เครื่องมือในเครื่องตีกัน:** การรัน MCP หลายตัวมักต้องติดตั้งทั้ง Node.js (`npx`), Python (`uvx`) และจัดการ Dependency ต่างๆ ลงในเครื่องหลักโดยตรง
* **แก้ไขยุ่งยาก:** ทุกครั้งที่ต้องการปิดใช้งาน MCP ชั่วคราวหรือแก้ API Key ต้องเปิดไฟล์ JSON แก้เองและรีสตาร์ทโปรแกรมใหม่

### สิ่งที่ Adison MCP Gateway เข้ามาแก้ไข
* **Single Endpoint (`/mcp`):** รวมเครื่องมือ (Tools) จาก MCP Server ภายนอกทั้งหมดไว้ที่จุดเดียวผ่านมาตรฐาน **Streamable HTTP** (`http://localhost:8000/mcp`) นำไปเชื่อมต่อกับ AI Agent เพียงครั้งเดียวจบ
* **Web Admin Dashboard (`/admin`):** มีหน้าเว็บสำหรับวาง JSON Config เพื่อเพิ่ม แก้ไข ลบ หรือกดสวิตช์เปิด-ปิด MCP ชั่วคราว พร้อมระบบ **Hot-Reload** โหลดเครื่องมือใหม่เข้าสู่ระบบทันทีโดยไม่ต้องรีสตาร์ท Container
* **Isolated Environment (Docker):** รันทุกอย่างภายใน Docker Container ที่เตรียมสภาพแวดล้อมทั้ง Python (`uv` / `uvx`) และ Node.js (`npx`) ไว้พร้อมใช้งาน ไม่รบกวนเครื่องหลัก
* **ปลอดภัยด้วย `.env` & Auto-Backup:** รองรับการดึงรหัสผ่านผ่านตัวแปร `${VAR_NAME}` จากไฟล์ `.env` และสำรองไฟล์ Config เป็น `.bak` อัตโนมัติทุกครั้งที่มีการแก้ไขผ่านหน้าเว็บ

---

## 2. สิ่งที่ต้องเตรียมก่อนติดตั้ง (Prerequisites)

1. **Git** สำหรับดาวน์โหลดซอร์สโค้ด
2. **Docker Desktop** (เปิดโปรแกรมให้พร้อมใช้งานก่อนเริ่มติดตั้ง)

---

## 3. ขั้นตอนการติดตั้ง (Installation)

เปิด Terminal / Command Prompt แล้วทำตามลำดับดังนี้:

### ขั้นตอนที่ 1: Clone โปรเจกต์
```bash
git clone https://github.com/MrAdisonbb2/Adison_MCP_Server.git
cd Adison_MCP_Server
```

### ขั้นตอนที่ 2: สร้างไฟล์ตั้งค่าเริ่มต้น (`.env` และ `mcp_servers.json`)
คัดลอกไฟล์ตัวอย่างเพื่อสร้างไฟล์ใช้งานจริงในเครื่อง (สำคัญ: ต้องสร้างไฟล์ `mcp_servers.json` ก่อนรัน Docker เพื่อป้องกันไม่ให้ Docker สร้างเป็นโฟลเดอร์แทนไฟล์):

* **สำหรับ Windows (CMD):**
  ```cmd
  copy .env.example .env
  copy mcp_servers.example.json mcp_servers.json
  ```
* **สำหรับ macOS / Linux:**
  ```bash
  cp .env.example .env
  cp mcp_servers.example.json mcp_servers.json
  ```

*(ทางเลือก)* เปิดไฟล์ `.env` เพื่อใส่ API Keys ที่ต้องใช้งาน เช่น `NOTION_API_KEY=...` หรือ `GITHUB_TOKEN=...`

### ขั้นตอนที่ 3: Build และเริ่มรันระบบด้วย Docker
```bash
docker compose up -d --build
```
รอจนกระทั่ง Docker สร้าง Image และสตาร์ท Container `adison-mcp-server` เสร็จสิ้น

---

## 4. วิธีการใช้งาน (Usage)

ระบบแบ่งช่องทางการใช้งานออกเป็น **2 ส่วน** บนพอร์ต `8000` เดียวกัน:

### ส่วนที่ 1: จัดการ MCP Servers ผ่านหน้าเว็บ (สำหรับผู้ใช้งาน)
1. เปิดเบราว์เซอร์แล้วเข้าไปที่ **`http://localhost:8000/admin`** (หรือ `http://localhost:8000`)
2. **การเพิ่ม MCP ใหม่:**
   * กดปุ่ม **`+ เพิ่ม MCP ใหม่`**
   * วาง JSON Config ที่ได้มาจาก GitHub หรือเอกสารของ MCP ตัวนั้นลงในกล่องข้อความ (ระบบรองรับทั้งการวางเฉพาะบล็อก `"command": ...` หรือวางครอบทั้ง `{"mcpServers": {...}}`)
   * กด **`บันทึกและโหลดใช้งาน`** ระบบจะบันทึกไฟล์และเชื่อมต่อ MCP ตัวใหม่ทันที
   * *ตัวอย่าง JSON สำหรับเพิ่ม MCP:*
     ```json
     {
       "time": {
         "command": "uvx",
         "args": ["mcp-server-time"]
       }
     }
     ```
3. **การแก้ไข / เปิด-ปิดชั่วคราว / ลบ:**
   * **ปิดชั่วคราว:** กดปุ่ม `ปิดชั่วคราว` บนการ์ดเพื่อซ่อนเครื่องมือของ MCP ตัวนั้นจาก AI Agent โดยไม่ต้องลบ Config ทิ้ง
   * **แก้ไข:** กดปุ่ม `แก้ไข` เพื่อปรับแต่งคำสั่ง `args`, `url` หรือตัวแปร `env`
   * **ลบ:** กดปุ่ม `ลบ` เพื่อนำ MCP ออกจากระบบถาวร
   * **Reload MCPs:** กดปุ่ม `↻ Reload MCPs` มุมขวาบนเพื่อบังคับเชื่อมต่อ MCP ทั้งหมดใหม่อีกครั้ง (เช่น หลังแก้ไขค่าในไฟล์ `.env`)

---

### ส่วนที่ 2: เชื่อมต่อเข้ากับ AI Agent (Streamable HTTP)

นำ Endpoint **`http://localhost:8000/mcp`** ไปใส่ในไฟล์ตั้งค่าของ AI Agent ที่ใช้งานอยู่:

#### 1. Google Antigravity
เปิดเมนู **Agent** > **`...`** > **MCP Servers** > **Manage MCP Servers** > **View raw config** (`mcp_config.json`) แล้ววาง Config นี้:
```json
{
  "mcpServers": {
    "adison-mcp": {
      "serverUrl": "http://localhost:8000/mcp"
    }
  }
}
```
จากนั้นกดปุ่ม **Refresh** ในหน้า Manage MCP Servers

#### 2. Cursor / Windsurf / Cline / Roo Code
นำไปวางในหน้าตั้งค่า MCP Settings ของโปรแกรม:
```json
{
  "mcpServers": {
    "adison-mcp": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

#### 3. กรณีเชื่อมต่อข้ามเครื่อง (เช่น ผ่าน Tailscale หรือวง LAN)
1. เปิดไฟล์ `docker-compose.yml` และแก้บรรทัด `ports:` จาก `"127.0.0.1:8000:8000"` เป็น `"8000:8000"` (หรือระบุ IP ของ Tailscale) แล้วรัน `docker compose up -d`
2. เปลี่ยน `localhost` ในการตั้งค่าของ AI Agent เป็น IP ของเครื่องที่รัน Docker เช่น `http://100.x.y.z:8000/mcp`

---

## 5. คำสั่งจัดการระบบ (Maintenance)

* **ดู Log การทำงานของระบบและสถานะการเชื่อมต่อ MCP:**
  ```bash
  docker logs -f adison-mcp-server
  ```
* **หยุดการทำงานชั่วคราว (ไม่ลบ Container):**
  ```bash
  docker compose stop
  ```
* **เปิดกลับมาใช้งานอีกครั้ง:**
  ```bash
  docker compose start
  ```
* **รีสตาร์ทระบบ (เช่น หลังแก้ไฟล์ `.env`):**
  ```bash
  docker compose restart
  ```

---

## 6. วิธีการลบและถอนการติดตั้ง (Uninstallation)

หากไม่ต้องการใช้งานโปรเจกต์นี้แล้ว สามารถลบ Container, Image และไฟล์ทั้งหมดออกจากเครื่องได้ตามขั้นตอนดังนี้:

1. **ปิดและลบ Docker Container พร้อม Network:**
   ```bash
   docker compose down
   ```
2. **ลบ Docker Image ของโปรเจกต์ (เพื่อคืนพื้นที่ฮาร์ดดิสก์):**
   ```bash
   docker compose down --rmi all
   ```
3. **ลบโฟลเดอร์โปรเจกต์ออกจากเครื่อง:**
   ถอยออกมา 1 โฟลเดอร์ (`cd ..`) แล้วลบโฟลเดอร์ `Adison_MCP_Server` ทิ้งได้ทันที