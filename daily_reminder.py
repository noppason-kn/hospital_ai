# from prefect import flow, task
# from datetime import datetime
# from db.db import db
# from backend.line_service import LineNotifier

# notifier = LineNotifier()

# def get_thai_month(date_obj):
#     months = [
#         "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
#         "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
#     ]
#     return f"{date_obj.day} {months[date_obj.month - 1]} {date_obj.year + 543}"

# @task(log_prints=True)
# def send_daily_notifications():
#     today = datetime.now()
    
#     # 1. ดึงรายการ Active ทั้งหมดมาเป็น List ก่อน
#     active_records = list(db.medication_status.find({
#         "status": "active",
#         "end_date_raw": {"$gt": today}
#     }))

#     # 2. จัดกลุ่มข้อมูลตามชื่อคนไข้ (Group by patient_name)
#     # เผื่ออนาคตระบบมีคนไข้หลายคน จะได้แยกบับเบิ้ลตามคน
#     patient_buckets = {}
#     for record in active_records:
#         name = record.get("patient_name", "คุณตา/คุณยาย")
#         if name not in patient_buckets:
#             patient_buckets[name] = []
#         patient_buckets[name].append(record)

#     # 3. วนลูปส่ง LINE ตามรายชื่อคนไข้ (1 คน = 1 บับเบิ้ล)
#     for patient_name, records in patient_buckets.items():
#         msg_header = f"สวัสดีตอนเช้าค่ะคุณ{patient_name} \nวันนี้อย่าลืมทานยานะคะ"
#         med_details = ""
        
#         for i, rec in enumerate(records, 1):
#             end_date_raw = rec["end_date_raw"]
#             days_left = (end_date_raw - today).days + 1
#             end_date_thai = get_thai_month(end_date_raw)
            
#             # ดึงข้อมูลนัดหมาย (ถ้ามี)
#             appt_date = rec.get("follow_up_date", "ไม่มีนัด")
            
#             # ถ้ามีหลายรายการ ให้ใส่เลขข้อ
#             prefix = f"\nชุดที่ {i}:" if len(records) > 1 else ""
#             med_details += (
#                 f"{prefix}\n"
#                 f"💊 เหลือยาอีก {days_left} วัน (หมด {end_date_thai})\n"
#                 f"📅 นัดครั้งหน้า: {appt_date}\n"
#             )
            
#             # Logic ปิดสถานะ (ยังคงไว้เหมือนเดิม)
#             if days_left <= 1:
#                 db.medication_status.update_one(
#                     {"_id": rec["_id"]},
#                     {"$set": {"status": "completed", "reason": "ทานยาครบกำหนด"}}
#                 )

#         final_msg = f"{msg_header}\n{med_details}\n"
        
#         # ส่ง LINE แค่ครั้งเดียวต่อคน
#         success = notifier.send_push(final_msg)
#         if success:
#             print(f"✅ มัดรวมส่งแจ้งเตือนให้ {patient_name} เรียบร้อย ({len(records)} รายการ)")

# @flow(name="Medication Daily Reminder Flow")
# def medication_reminder_flow():
#     send_daily_notifications()

# if __name__ == "__main__":
#     # ตั้งให้รันทุกวัน (Cron) ตอน 9 โมงเช้า
#     medication_reminder_flow.serve(
#         name="daily-med-reminder-9am",
#         cron="0 9 * * *" 
#     )
    
    
from prefect import flow, task
from datetime import datetime
from db.db import db
from backend.line_service import LineNotifier

notifier = LineNotifier()

def get_thai_month(date_obj):
    months = [
        "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]
    return f"{date_obj.day} {months[date_obj.month - 1]} {date_obj.year + 543}"

# --- ฟังก์ชันช่วยแปลงวันที่เพิ่มเติมนิดหน่อย ---
def format_thai_date(date_str):
    if not date_str or date_str == "ไม่มีการนัด":
        return "ยังไม่มีนัดใหม่ค่ะ"
    try:
        # กรณีวันที่มาเป็น ISO (2026-05-15)
        dt = datetime.strptime(date_str.split('T')[0], "%Y-%m-%d")
        return get_thai_month(dt)
    except:
        return date_str # ถ้าแปลงไม่ได้ให้ส่งค่าเดิม

@task(log_prints=True)
def send_daily_notifications():
    today = datetime.now()
    
    # 1. ดึงรายการ Active
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

    # 3. วนลูปสร้างข้อความ
    for patient_name, records in patient_buckets.items():
        msg_header = f"สวัสดีตอนเช้าค่ะคุณ{patient_name} ❤️\n"
        med_details = ""
        
        for i, rec in enumerate(records, 1):
            # --- ดึงชื่อโรคมาทำหัวข้อ (แทนคำว่าชุดที่) ---
            visit_data = db.visits.find_one({"_id": rec["visit_id"]})
            diag_name = "ยาทั่วไป"
            if visit_data:
                diag = visit_data.get("diagnosis", ["ยา"])
                diag_name = diag[0] if isinstance(diag, list) else diag

            end_date_raw = rec["end_date_raw"]
            diff = end_date_raw - today
            days_left = diff.days + 1
            
            end_date_thai = get_thai_month(end_date_raw)
            # แปลงวันนัดให้เป็น พ.ศ. ไทย
            appt_date_thai = format_thai_date(rec.get("follow_up_date"))
            
            # --- สร้างเนื้อหาแบบเน้นๆ ---
            med_details += (
                f"\n🔴 {diag_name}:\n"
                f"💊 กินได้ถึงวันที่: {end_date_thai}\n"
                f"📅 หมอนัดวันที่: {appt_date_thai}\n"
            )
            
            # ปิดสถานะ
            if days_left <= 0:
                db.medication_status.update_one(
                    {"_id": rec["_id"]},
                    {"$set": {"status": "completed", "reason": "ทานยาครบกำหนด"}}
                )

        # 4. ประกอบร่างข้อความสุดท้าย (เพิ่มคำแนะนำสั้นๆ)
        final_msg = (
            f"{msg_header}"
            f"{med_details}\n"
            f"ใกล้หมดแล้วอย่าลืมเตรียมตัวไปหาหมอนะคะ พยาบาลเป็นห่วงค่ะ ✨"
        )
        
        notifier.send_push(final_msg)

@flow(name="Medication Daily Reminder Flow")
def medication_reminder_flow():
    send_daily_notifications()

# --- จุดสำคัญ: เปลี่ยนจาก .serve() เป็นการรันฟังก์ชันตรงๆ ---
if __name__ == "__main__":
    print("🚀 กำลังรัน Manual Test...")
    medication_reminder_flow() # เรียกใช้งานทันที
    