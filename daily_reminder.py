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
    """งานหลัก: ตรวจสอบยาและวันนัดหมาย เพื่อส่งแจ้งเตือน LINE"""
    try:
        from db.db import db
        from backend.line_service import LineNotifier
        from backend.helper import format_thai_date
    except ImportError as e:
        print(f"❌ ไม่สามารถโหลดโมดูลภายในได้: {e}")
        return

    notifier = LineNotifier()
    today = datetime.now(timezone.utc)
    
    print(f"🚀 เริ่มกระบวนการตรวจสอบข้อมูลประจำวันที่: {today.strftime('%Y-%m-%d %H:%M:%S')} (UTC)")
    
    try:
        # 1. ค้นหารายการยาที่ยังมีสถานะ 'active'
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
        msg_header = f"สวัสดีตอนเช้าค่ะคุณ {patient_name} ☀️\n"
        med_details = "📋 รายการยาที่ต้องทานวันนี้:"
        appointment_info = ""
        warning_info = ""
        
        # เก็บ Visit ID ที่ประมวลผลไปแล้วเพื่อไม่ให้วันนัดซ้ำซ้อน
        processed_visits = set()

        for rec in records:
            visit_id = rec["visit_id"]
            visit_data = db.visits.find_one({"_id": visit_id})
            
            # --- ส่วนของยา ---
            diag_label = "รายการยา"
            if visit_data:
                diag = visit_data.get("diagnosis", visit_data.get("symptoms", ["ทั่วไป"]))
                diag_label = diag[0] if isinstance(diag, list) else diag
            
            end_date_thai = format_thai_date(rec["end_date_raw"])
            med_details += f"\n🔴 {diag_label}:\n   💊 ทานถึง: {end_date_thai}"

            # --- ส่วนของวันนัด (ทำครั้งเดียวต่อหนึ่งใบสั่งยา) ---
            if visit_id not in processed_visits and visit_data:
                follow_up = visit_data.get("follow_up_date")
                if follow_up and follow_up != "-":
                    appointment_info = f"\n\n📅 วันนัดครั้งถัดไป:\n📍 {follow_up}"
                
                # --- ส่วนของอาการเตือน ---
                warnings = visit_data.get("warning_symptoms", [])
                if warnings and isinstance(warnings, list):
                    warning_info = f"\n\n⚠️ หากมีอาการ: {', '.join(warnings)} ให้รีบมาพบแพทย์ทันทีนะคะ"
                
                processed_visits.add(visit_id)

        final_msg = f"{msg_header}\n{med_details}{appointment_info}{warning_info}\n\nอย่าลืมดูแลสุขภาพนะคะ ✨"
        
        try:
            notifier.send_push(final_msg)
            print(f"✅ ส่งแจ้งเตือนพร้อมวันนัดให้ {patient_name} สำเร็จ")
        except Exception as e:
            print(f"❌ ส่งล้มเหลวให้ {patient_name}: {e}")

@flow(name="Medication Daily Reminder Flow")
def medication_reminder_flow():
    send_daily_notifications()

if __name__ == "__main__":
    print("⏳ กำลังเตรียมระบบ (Waiting for 15s)...")
    time.sleep(15)
    
    print("-----------------------------------------")
    print(f"🕒 เริ่มระบบแจ้งเตือน (Target: 09:00 น. เวลาไทย)")
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