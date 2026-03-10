# ใช้ Python 3.12-slim เป็นพื้นฐาน
FROM python:3.12-slim

# 🟢 เพิ่มการติดตั้ง curl เพื่อใช้ในการเช็กสถานะ Health ของ Prefect Server ใน Docker Compose
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# ตั้งค่า Working Directory
WORKDIR /app

# ติดตั้ง dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโค้ดทั้งหมด
COPY . .

# กำหนด Default command
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]