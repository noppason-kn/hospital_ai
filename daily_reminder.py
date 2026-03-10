import os
import sys
from datetime import datetime
from prefect import flow, task
from prefect.schedules import Cron

# 🟢 แก้ไขจุดที่ผิด: ต้องใช้ os.path.abspath และ os.path.join
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@task(log_prints=True)
def send_daily_notifications():
    """งานหลักในการตรวจสอบฐานข้อมูลและส่งการแจ้งเตือน LINE"""
    try:
        # โหลดโมดูลภายในโครงการ
        from db.db import db
        from backend.line_service import LineNotifier
        from backend.helper import format_thai_date
    except ImportError as e:
        print(f"❌ ไม่สามารถโหลดโมดูลภายในได้: {e}")
        return

    notifier = LineNotifier()
    today = datetime.now()
    
    print(f"🚀 เริ่มกระบวนการตรวจสอบการแจ้งเตือนประจำวันที่: {today}")
    
    # ค้นหารายการยาที่ยังมีสถานะ 'active'
    active_records = list(db.medication_status.find({
        "status": "active",
        "end_date_raw": {"$gte": today.replace(hour=0, minute=0, second=0)}
    }))

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

    # วนลูปส่งข้อความ
    for patient_name, records in patient_buckets.items():
        msg_header = f"สวัสดีตอนเช้าค่ะคุณ {patient_name} ☀️\n"
        med_details = ""
        
        for rec in records:
            visit_data = db.visits.find_one({"_id": rec["visit_id"]})
            diag_label = "รายการยา"
            if visit_data:
                diag = visit_data.get("diagnosis", visit_data.get("symptoms", "ทั่วไป"))
                diag_label = diag[0] if isinstance(diag, list) else diag

            end_date_thai = format_thai_date(rec["end_date_raw"])
            med_details += f"\n🔴 {diag_label}:\n💊 ทานต่อเนื่องถึง: {end_date_thai}\n"

        final_msg = f"{msg_header}{med_details}\nอย่าลืมทานยาให้ตรงเวลาตามที่หมอสั่งนะคะ ✨"
        
        try:
            notifier.send_push(final_msg)
            print(f"✅ ส่งข้อความให้ {patient_name} สำเร็จ")
        except Exception as e:
            print(f"❌ ส่งล้มเหลว: {e}")

@flow(name="Medication Daily Reminder Flow")
def medication_reminder_flow():
    """Flow หลักของ Prefect สำหรับระบบแจ้งเตือน"""
    send_daily_notifications()

if __name__ == "__main__":
    print("-----------------------------------------")
    print(f"🕒 เริ่มระบบแจ้งเตือน (Target: 09:00 น. เวลาไทย)")
    print("-----------------------------------------")
    
    # รัน Prefect ในโหมด Serve
    medication_reminder_flow.serve(
        name="medication-reminder-prod",
        schedule=Cron("0 9 * * *", timezone="Asia/Bangkok"),
        tags=["production", "gcp-deployment"]
    )
