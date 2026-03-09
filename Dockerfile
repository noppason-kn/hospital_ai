# ใช้ Python 3.12-slim ให้ตรงกับสภาพแวดล้อมที่คุณใช้งาน (3.12.2) เพื่อความเสถียรสูงสุด
FROM python:3.12-slim

# ตั้งค่า Working Directory
WORKDIR /app

# ติดตั้ง dependencies ที่จำเป็นสำหรับระบบ
# คัดลอกเฉพาะ requirements.txt มาก่อนเพื่อใช้ประโยชน์จาก Docker Layer Cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโค้ดทั้งหมดของโปรเจกต์เข้าไป
COPY . .

# กำหนด Default command (สามารถ override ได้ใน docker-compose)
# ในที่นี้เราจะตั้งค่าเริ่มต้นให้รันแอปหลัก (FastAPI/Uvicorn) เหมือนโค้ดเก่าของคุณ
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]