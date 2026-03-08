from prefect import flow, task
from datetime import datetime
from db.db import db
from backend.line_service import LineNotifier
from backend.helper import format_thai_date

notifier = LineNotifier()

@task(log_prints=True)
def send_daily_notifications():
    today = datetime.now()
    
    # 1. ดึงรายการ Active (กรองเฉพาะที่ยายังไม่หมดอายุ)
    active_records = list(db.medication_status.find({
        "status": "active",
        "end_date_raw": {"$gte": today.replace(hour=0, minute=0, second=0)}
    }))

    # 2. จัดกลุ่มตามชื่อคนไข้
    patient_buckets = {}
    for record in active_records:
        name = record.get("patient_name", "คุณตา/คุณยาย")
        if name not in patient_buckets: patient_buckets[name] = []
        patient_buckets[name].append(record)

    # 3. วนลูปสร้างข้อความแจ้งเตือน
    for patient_name, records in patient_buckets.items():
        msg_header = f"สวัสดีตอนเช้าค่ะคุณ {patient_name} \n"
        med_details = ""
        
        for i, rec in enumerate(records, 1):
            # --- ดึงข้อมูลจากฐานข้อมูลจริง (Visits Collection) ---
            visit_data = db.visits.find_one({"_id": rec["visit_id"]})
            
            # 🟢 ปิดการ Mock: ดึงชื่อโรคจาก diagnosis หรือใช้ชื่ออาการ (symptom) แทน
            topic_name = "รายการยา" 
            if visit_data:
                diag = visit_data.get("diagnosis")
                symptom = visit_data.get("symptom")
                
                if diag:
                    # ถ้า diagnosis เป็น list ให้หยิบตัวแรก ถ้าเป็น string ให้ใช้เลย
                    topic_name = diag[0] if isinstance(diag, list) else diag
                elif symptom:
                    # ถ้าไม่มีชื่อโรค ให้ใช้ชื่ออาการแทนเพื่อให้คนไข้เข้าใจง่าย
                    topic_name = symptom

            end_date_raw = rec["end_date_raw"]
            diff = end_date_raw - today
            days_left = diff.days + 1
            
            end_date_thai = format_thai_date(rec["end_date_raw"]) 
            appt_date_thai = format_thai_date(rec.get("follow_up_date")) 
            
            # --- สร้างเนื้อหาข้อความ ---
            med_details += (
                f"\n🔴 {topic_name}:\n"
                f"💊 กินได้ถึงวันที่: {end_date_thai}\n"
                f"📅 หมอนัดวันที่: {appt_date_thai}\n"
            )
            
            # ปิดสถานะอัตโนมัติเมื่อทานยาครบ
            if days_left <= 0:
                db.medication_status.update_one(
                    {"_id": rec["_id"]},
                    {"$set": {"status": "completed", "reason": "ทานยาครบกำหนด"}}
                )

        # 4. ประกอบร่างข้อความสุดท้าย
        final_msg = (
            f"{msg_header}"
            f"{med_details}\n"
            f"ใกล้หมดแล้วอย่าลืมเตรียมตัวไปหาหมอนะคะ พยาบาลเป็นห่วงค่ะ ✨"
        )
        
        # ส่งแจ้งเตือนผ่าน LINE
        notifier.send_push(final_msg)

@flow(name="Medication Daily Reminder Flow")
def medication_reminder_flow():
    send_daily_notifications()

if __name__ == "__main__":
    print("🚀 กำลังรันระบบแจ้งเตือนจริงจากฐานข้อมูล...")
    medication_reminder_flow()

