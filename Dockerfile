FROM python:3.11-slim

WORKDIR /app

# ป้องกัน Python สร้างไฟล์ .pyc และให้แสดง Log ออกทาง Console ทันที
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# คัดลอกไฟล์กำหนดค่าและซอร์สโค้ด
COPY pyproject.toml README.md ./
COPY src/ ./src/

# ติดตั้ง Dependencies
RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["python", "-m", "src.server"]