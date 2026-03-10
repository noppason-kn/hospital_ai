import os
import sys
import time
from datetime import datetime, timezone
from prefect import flow, task
from prefect.schedules import Cron

# 🟢 จัดการ Path ให้มองเห็นโมดูลภายใน (db, backend)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
PARENT_DIR = os.path.dirname(BASE_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

@task(log_prints=True, retries=3, retry_delay_seconds=30)
def send_daily_notifications():
    """งานหลัก: ส่งแจ้งเตือน LINE พร้อมอิโมจิและโครงสร้างที่นายต้องการ"""
    try:
        from db.db import db
        from backend.line_service import LineNotifier
        from backend.helper import format_thai_date
    except ImportError as e:
        print(f"❌ ไม่สามารถโหลดโมดูลภายในได้: {e}")
        return

    notifier = LineNotifier()
    today = datetime.now(timezone.utc)
    
    print(f"🚀 เริ่มตรวจสอบข้อมูลประจำวันที่: {today.strftime('%Y-%m-%d %H:%M:%S')} (UTC)")
    
    try:
        # ค้นหารายการยาที่ยังมีสถานะ 'active'
        active_records = list(db.medication_status.find({
            "status": "active",
            "end_date_raw": {"$gte": today.replace(hour=0, minute=0, second=0, microsecond=0)}
        }))
    except Exception as e:
        print(f"❌ ติดปัญหาการดึงข้อมูลจาก Database: {e}")
        return

    if not active_records:
        print("📭 ไม่มีรายการแจ้งเตือนสำหรับวันนี้")
        return

    # จัดกลุ่มข้อมูลตามคนไข้
    patient_buckets = {}
    for record in active_records:
        name = record.get("patient_name", "คุณตา/คุณยาย")
        if name not in patient_buckets:
            patient_buckets[name] = []
        patient_buckets[name].append(record)

    for patient_name, records in patient_buckets.items():
        # 1. ส่วนหัวข้อ (Greeting) พร้อมอิโมจิ
        msg = f"สวัสดีตอนเช้าค่ะคุณ {patient_name} ☀️\n"
        
        # 2. ส่วนรายละเอียด (Diagnosis + Med Date + Appointment Date)
        for rec in records:
            visit_id = rec["visit_id"]
            visit_data = db.visits.find_one({"_id": visit_id})
            
            # ดึงชื่อโรค/การวินิจฉัย
            diag_label = "รายการยา"
            follow_up_display = "ไม่มีนัดหมาย"
            
            if visit_data:
                diag = visit_data.get("diagnosis", visit_data.get("symptoms", ["ทั่วไป"]))
                diag_label = diag[0] if isinstance(diag, list) else diag
                
                # ดึงวันนัดหมาย
                follow_up = visit_data.get("follow_up_date")
                if follow_up and follow_up != "-":
                    follow_up_display = follow_up
            
            # ดึงวันหมดอายุยา
            end_date_thai = format_thai_date(rec["end_date_raw"])
            
            # ต่อสตริงตามโครงสร้างพร้อมไอคอน
            msg += f"\n🔴 {diag_label}:\n💊 กินได้ถึงวันที่: {end_date_thai}\n📅 หมอนัดวันที่: {follow_up_display}\n"

        # 3. ส่วนท้าย (Footer)
        msg += "\nใกล้หมดแล้วอย่าลืมเตรียมตัวไปหาหมอนะคะ ผู้ช่วยเป็นห่วงค่ะ ✨"
        
        try:
            notifier.send_push(msg)
            print(f"✅ [LINE SUCCESS] ส่งให้ {patient_name} สำเร็จ")
            print(f"DEBUG MSG:\n{msg}") 
        except Exception as e:
            print(f"❌ [LINE FAILED] ส่งให้ {patient_name} พลาด: {e}")

@flow(name="Medication Daily Reminder Flow")
def medication_reminder_flow():
    send_daily_notifications()

if __name__ == "__main__":
    # รอระบบ Docker นิ่ง
    print("⏳ กำลังเตรียมระบบ (Waiting for 15s)...")
    time.sleep(15)
    
    print("-----------------------------------------")
    print(f"🕒 เริ่มระบบแจ้งเตือน (Schedule: 09:00 AM BKK)")
    print(f"📅 เวลาเครื่องปัจจุบัน (UTC): {datetime.now(timezone.utc)}")
    print("-----------------------------------------")
    
    try:
        medication_reminder_flow.serve(
            name="medication-reminder-prod",
            schedule=Cron("* * * * *", timezone="Asia/Bangkok"),
            tags=["production", "gcp-deployment"]
        )
    except Exception as e:
        print(f"💥 เกิดข้อผิดพลาดร้ายแรง: {e}")