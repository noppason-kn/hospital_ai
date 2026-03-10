import os
import sys
import time
from datetime import datetime, timezone
from prefect import flow, task
from prefect.schedules import Cron

# 🟢 จัดการ Path ให้มองเห็นโมดูลภายใน (db, backend) อย่างแม่นยำ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
PARENT_DIR = os.path.dirname(BASE_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

@task(log_prints=True, retries=3, retry_delay_seconds=30)
def send_daily_notifications():
    """งานหลัก: ส่งแจ้งเตือน LINE พร้อมข้อมูลการรักษาและนัดหมาย (เวอร์ชันเสถียรที่สุด)"""
    try:
        from db.db import db
        from backend.line_service import LineNotifier
        from backend.helper import format_thai_date
    except ImportError as e:
        print(f"❌ [CRITICAL] ไม่สามารถโหลดโมดูลภายในได้: {e}")
        return

    notifier = LineNotifier()
    today = datetime.now(timezone.utc)
    
    print(f"🚀 เริ่มกระบวนการตรวจสอบข้อมูลประจำวันที่: {today.strftime('%Y-%m-%d %H:%M:%S')} (UTC)")
    
    try:
        # 1. ค้นหารายการยาที่ยังมีสถานะ 'active' และวันหมดยายังไม่ถึง
        active_records = list(db.medication_status.find({
            "status": "active",
            "end_date_raw": {"$gte": today.replace(hour=0, minute=0, second=0, microsecond=0)}
        }))
        print(f"📊 พบรายการยาที่กำลังใช้งาน (Active): {len(active_records)} รายการ")
    except Exception as e:
        print(f"❌ [DB ERROR] ติดปัญหาการดึงข้อมูลจาก Database: {e}")
        return

    if not active_records:
        print("📭 ไม่มีรายการแจ้งเตือนสำหรับวันนี้ (ทุกรายการจบการรักษาแล้วหรือยังไม่มีข้อมูล)")
        return

    # 2. จัดกลุ่มข้อมูลตามคนไข้ (Patient Bucketing)
    patient_buckets = {}
    for record in active_records:
        name = record.get("patient_name", "คุณตา/คุณยาย")
        if name not in patient_buckets:
            patient_buckets[name] = []
        patient_buckets[name].append(record)

    # 3. วนลูปส่งแจ้งเตือนรายคน
    for patient_name, records in patient_buckets.items():
        msg = f"สวัสดีตอนเช้าค่ะคุณ {patient_name} ☀️\n"
        
        for rec in records:
            visit_id = rec["visit_id"]
            visit_data = db.visits.find_one({"_id": visit_id})
            
            # --- ดึงชื่อโรค/การวินิจฉัย ---
            diag_label = "รายการยา"
            follow_up_display = "ยังไม่มีนัดหมายใหม่ค่ะ"
            
            if visit_data:
                diag = visit_data.get("diagnosis", visit_data.get("symptoms", ["ทั่วไป"]))
                diag_label = diag[0] if isinstance(diag, list) else diag
                
                # --- จัดการเรื่องวันนัดและเวลา ---
                follow_up_raw = visit_data.get("follow_up_date")
                follow_up_time_val = visit_data.get("follow_up_time")
                
                if follow_up_raw and follow_up_raw != "-":
                    # แปลงเป็นวันที่ไทย
                    follow_up_display = format_thai_date(follow_up_raw)
                    # ถ้ามีเวลา ให้ใส่ "เวลา ... น." ต่อท้าย
                    if follow_up_time_val and follow_up_time_val != "-":
                        follow_up_display += f" เวลา {follow_up_time_val} น."
            
            # --- แปลงวันยาหมดเป็นภาษาไทย ---
            end_date_thai = format_thai_date(rec.get("end_date_raw"))
            
            # --- ประกอบข้อความรายโรค ---
            msg += f"\n🔴 {diag_label}:\n💊 กินได้ถึงวันที่: {end_date_thai}\n📅 หมอนัดวันที่: {follow_up_display}\n"

        # ปิดท้ายข้อความ
        msg += "\nใกล้หมดแล้วอย่าลืมเตรียมตัวไปหาหมอนะคะ ผู้ช่วยเป็นห่วงค่ะ ✨"
        
        # 4. ส่งผ่าน LINE Notifier
        try:
            success = notifier.send_push(msg)
            if success:
                print(f"✅ [LINE SUCCESS] ส่งให้คุณ {patient_name} สำเร็จ")
            else:
                print(f"❌ [LINE FAILED] ส่งให้คุณ {patient_name} ไม่สำเร็จ (ตรวจสอบ Token หรือ User ID)")
        except Exception as e:
            print(f"💥 [ERROR] ระบบส่ง LINE ขัดข้องสำหรับ {patient_name}: {e}")

@flow(name="Medication Daily Reminder Flow")
def medication_reminder_flow():
    send_daily_notifications()

if __name__ == "__main__":
    # รอระบบพื้นฐาน (Docker/DB) ให้พร้อมรัน
    print("⏳ กำลังเตรียมระบบ (Waiting for 15s)...")
    time.sleep(15)
    
    print("-----------------------------------------")
    print(f"🕒 เริ่มระบบแจ้งเตือน (Target: 09:00 AM BKK)")
    print(f"📅 เวลาเครื่องปัจจุบัน (UTC): {datetime.now(timezone.utc)}")
    print("-----------------------------------------")
    
    try:
        # สั่งให้ Flow เริ่มทำงานตามตารางเวลา (Cron)
        medication_reminder_flow.serve(
            name="medication-reminder-prod",
            schedule=Cron("0 9 * * *", timezone="Asia/Bangkok"),
            tags=["production", "gcp-deployment"]
        )
    except Exception as e:
        print(f"💥 เกิดข้อผิดพลาดร้ายแรงในการ Start Server: {e}")