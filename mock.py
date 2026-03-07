from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGO_URI)
db = client["hospital_ai_db"]

visits = db["visits"]
med_status = db["medication_status"]

visits.delete_many({})
med_status.delete_many({}) 
print("🗑️ Cleared old records...")

# ปรับ visit_datetime ให้เป็นช่วงต้นเดือนมีนาคม 2026 ทั้งหมดเพื่อความสดใหม่
data = [
    {
        "patient_name": "บุญมี ศรีสุข",
        "sex": "ผู้ชาย",
        "hn": "HN-54321",
        "age": 72,
        "visit_id": "V-20260301-001",
        "visit_datetime": "2026-03-01",
        "hospital_name": "โรงพยาบาลรักษ์คุณตาคุณยาย",
        "department": "แผนกอายุรกรรมทั่วไป",
        "doctor_name": "นพ. สมศักดิ์ รักษาดี",
        "vital_signs": {"temperature": "38.5 °C", "blood_pressure": "120/80 mmHg", "heart_rate": "88 bpm"},
        "symptoms": ["ไอ", "มีไข้", "เจ็บคอ"],
        "diagnosis": ["ไข้หวัดทั่วไป"],
        "medications": [
            {
                "name": "Paracetamol 500mg",
                "common_name": "ยาลดไข้ (พารา)",
                "total_amount": 40, # เพิ่มจำนวนยาให้กินได้นานขึ้น
                "morning": 1, "afternoon": 1, "evening": 1, "before_bed": 0,
                "dosage_instruction": "รับประทานครั้งละ 1 เม็ด เช้า กลางวัน เย็น (หลังอาหาร)"
            }
        ],
        "doctor_advice": ["พักผ่อนให้เพียงพอ", "ดื่มน้ำอุ่นมากๆ"],
        "activity_restriction": ["งดออกกำลังกายหนัก"],
        "diet_restriction": ["งดน้ำเย็น"],
        "warning_symptoms": ["ไข้สูงเกิน 3 วัน", "หายใจลำบาก"],
        "follow_up_date": "ไม่มีการนัด",
        "ipd_admission": {"is_admitted": False}
    },
    {
        "patient_name": "บุญมี ศรีสุข",
        "sex": "ผู้ชาย",
        "hn": "HN-54321",
        "age": 72,
        "visit_id": "V-20260305-001",
        "visit_datetime": "2026-03-05", # อนาคตจากอันเก่า
        "hospital_name": "โรงพยาบาลรักษ์คุณตาคุณยาย",
        "department": "คลินิกโรคเรื้อรัง (NCDs)",
        "doctor_name": "พญ. วิภาดา ใจเย็น",
        "vital_signs": {"temperature": "36.8 °C", "blood_pressure": "160/95 mmHg", "heart_rate": "80 bpm"},
        "symptoms": ["เวียนศีรษะ", "ตึงต้นคอ"],
        "diagnosis": ["ความดันโลหิตสูง"],
        "medications": [
            {
                "name": "Amlodipine 5mg",
                "common_name": "ยาลดความดัน (เม็ดขาว)",
                "total_amount": 30,
                "morning": 1, "afternoon": 0, "evening": 0, "before_bed": 0,
                "dosage_instruction": "รับประทานครั้งละ 1 เม็ด หลังอาหารเช้าทุกวัน"
            }
        ],
        "doctor_advice": ["วัดความดันที่บ้านทุกเช้า"],
        "activity_restriction": ["ระวังการเปลี่ยนอิริยาบถเร็วๆ"],
        "diet_restriction": ["งดอาหารเค็มจัด"],
        "warning_symptoms": ["ปวดศีรษะรุนแรง", "แขนขาอ่อนแรง"],
        "follow_up_date": "2026-05-15",
        "ipd_admission": {"is_admitted": False}
    }
]

# แทรกข้อมูล Visits
inserted_visits = visits.insert_many(data)

# --- ส่วนสำคัญ: สร้างสถานะใน medication_status ให้พร้อมเด้ง LINE ---
for i, visit in enumerate(data):
    # 1. คำนวณวันยาหมดจากจำนวนยาจริง
    v_date = datetime.strptime(visit["visit_datetime"], "%Y-%m-%d")
    durations = []
    for med in visit["medications"]:
        daily = med["morning"] + med["afternoon"] + med["evening"] + med["before_bed"]
        if daily > 0:
            durations.append(med["total_amount"] / daily)
    
    min_days = min(durations) if durations else 0
    end_date_raw = v_date + timedelta(days=min_days)

    # 2. บันทึกลง medication_status เพื่อให้ Prefect ค้นหาเจอ
    med_status.insert_one({
        "visit_id": inserted_visits.inserted_ids[i],
        "patient_name": visit["patient_name"],
        "status": "active",
        "end_date_raw": end_date_raw, # ต้องเป็น BSON Date เพื่อใช้ $gt
        "follow_up_date": visit["follow_up_date"]
    })

print(f"✅ Inserted {len(data)} visits and prepared active medication status!")
print(f"🚀 ตอนนี้รัน python daily_reminder.py ได้เลย ข้อมูลจะเด้งแน่นอน!")