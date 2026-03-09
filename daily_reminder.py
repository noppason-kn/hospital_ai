from prefect import flow, task
from prefect.schedules import Cron
from datetime import datetime
import time
# from db.db import db  <-- ย้ายออกไปจาก Global
from backend.line_service import LineNotifier
from backend.helper import format_thai_date

@task(log_prints=True)
def send_daily_notifications():
    """
    งานสำหรับดึงข้อมูลและส่งแจ้งเตือนคนไข้รายบุคคล
    """
    # 🟢 ย้ายมา Import และสร้างข้างใน Task เพื่อเลี่ยงปัญหา SSLContext Pickle Error
    from db.db import db
    notifier = LineNotifier()
    today = datetime.now()
    
    # 1. ดึงรายการที่สถานะยังคง Active และยายังไม่หมดอายุ
    active_records = list(db.medication_status.find({
        "status": "active",
        "end_date_raw": {"$gte": today.replace(hour=0, minute=0, second=0)}
    }))

    # 2. จัดกลุ่มข้อมูลตามชื่อคนไข้
    patient_buckets = {}
    for record in active_records:
        name = record.get("patient_name", "คุณตา/คุณยาย")
        if name not in patient_buckets: 
            patient_buckets[name] = []
        patient_buckets[name].append(record)

    # 3. วนลูปเพื่อสร้างข้อความแจ้งเตือนตามรายชื่อ
    for patient_name, records in patient_buckets.items():
        msg_header = f"สวัสดีตอนเช้าค่ะคุณ {patient_name} ☀️\n"
        med_details = ""
        
        for rec in records:
            # ดึงข้อมูลการตรวจรักษาจาก visits เพื่อหาชื่อโรค/อาการ
            visit_data = db.visits.find_one({"_id": rec["visit_id"]})
            
            topic_name = "รายการยา" 
            if visit_data:
                diag = visit_data.get("diagnosis")
                symptom = visit_data.get("symptoms", visit_data.get("symptom"))
                
                if diag:
                    topic_name = diag[0] if isinstance(diag, list) else diag
                elif symptom:
                    # ปรับให้รองรับทั้ง list และ string
                    topic_name = symptom[0] if isinstance(symptom, list) else symptom

            end_date_raw = rec["end_date_raw"]
            diff = end_date_raw - today
            days_left = diff.days + 1
            
            end_date_thai = format_thai_date(rec["end_date_raw"]) 
            appt_date_thai = format_thai_date(rec.get("follow_up_date")) 
            
            med_details += (
                f"\n🔴 {topic_name}:\n"
                f"💊 ทานได้ถึงวันที่: {end_date_thai}\n"
                f"📅 หมอนัดครั้งถัดไป: {appt_date_thai}\n"
            )
            
            if days_left <= 0:
                db.medication_status.update_one(
                    {"_id": rec["_id"]},
                    {"$set": {"status": "completed", "reason": "ทานยาครบกำหนด"}}
                )

        final_msg = (
            f"{msg_header}"
            f"{med_details}\n"
            f"อย่าลืมดูแลสุขภาพและเตรียมตัวไปตามนัดนะคะ พยาบาลเป็นห่วงค่ะ ✨"
        )
        
        # ส่งแจ้งเตือนผ่าน LINE
        notifier.send_push(final_msg)

@flow(name="Medication Daily Reminder Flow")
def medication_reminder_flow():
    """
    Flow หลักสำหรับรันระบบแจ้งเตือน
    """
    send_daily_notifications()

if __name__ == "__main__":
    # สำหรับการทดสอบ (รันทุก 1 นาที) ให้ใช้ "*/1 * * * *"
    # สำหรับใช้งานจริง 9 โมงเช้า ให้ใช้ "0 9 * * *"
    medication_reminder_flow.serve(
        name="medication-reminder",
        schedule=Cron("0 9 * * *", timezone="Asia/Bangkok"),
        tags=["test", "notification"]
    )
