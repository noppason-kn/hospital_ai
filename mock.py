from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGO_URI)
db = client["hospital_ai_db"]

visits = db["visits"]

# ล้างข้อมูลเก่าทิ้งก่อน
visits.delete_many({})
print("🗑️ Cleared old records...")

data = [
    {
        "patient_name": "บุญมี ศรีสุข",
        "sex": "ผู้ชาย",
        "hn": "HN-54321",
        "age": 72,
        "visit_datetime": "2026-03-01",
        "hospital_name": "โรงพยาบาลรักษ์คุณตาคุณยาย",
        "department": "แผนกอายุรกรรมทั่วไป",
        "doctor_name": "นพ. สมศักดิ์ รักษาดี",
        "vital_signs": {
            "temperature": "38.5 °C",
            "blood_pressure": "120/80 mmHg",
            "heart_rate": "88 bpm"
        },
        "symptoms": ["ไอ", "มีไข้", "เจ็บคอ"],
        "diagnosis": ["ไข้หวัดทั่วไป"],
        "medications": [
            {
                "name": "Paracetamol 500mg",
                "purpose": "ลดไข้ บรรเทาปวด",
                "dosage_instruction": "รับประทานครั้งละ 1 เม็ด หลังอาหารเช้า กลางวัน เย็น เวลาที่มีอาการ"
            },
            {
                "name": "Bromhexine 8mg",
                "purpose": "ละลายเสมหะ",
                "dosage_instruction": "รับประทานครั้งละ 1 เม็ด หลังอาหารเช้า กลางวัน เย็น"
            }
        ],
        "doctor_advice": ["พักผ่อนให้เพียงพอ", "ดื่มน้ำอุ่นมากๆ", "ใส่หน้ากากอนามัยเวลาอยู่ร่วมกับผู้อื่น"],
        "activity_restriction": ["งดออกกำลังกายหนัก", "หลีกเลี่ยงการโดนลมหรือตากฝน"],
        "diet_restriction": ["งดน้ำเย็น", "งดอาหารทอดหรือมันเพราะจะทำให้ระคายคอ"],
        "warning_symptoms": ["ไข้สูงเกิน 3 วัน", "หายใจลำบาก หรือหอบเหนื่อย"],
        "follow_up_date": "ไม่มีการนัด",
        "medical_certificate": {
            "certificate_date": "2026-03-01",
            "rest_period": "2 วัน"
        },
        "ipd_admission": {"is_admitted": False}
    },
    {
        "patient_name": "บุญมี ศรีสุข",
        "sex": "ผู้ชาย",
        "hn": "HN-54321",
        "age": 72,
        "visit_datetime": "2026-02-15",
        "hospital_name": "โรงพยาบาลรักษ์คุณตาคุณยาย",
        "department": "คลินิกโรคเรื้อรัง (NCDs)",
        "doctor_name": "พญ. วิภาดา ใจเย็น",
        "vital_signs": {
            "temperature": "36.8 °C",
            "blood_pressure": "160/95 mmHg", 
            "heart_rate": "80 bpm"
        },
        "symptoms": ["เวียนศีรษะ", "ตึงต้นคอ", "หน้ามืดเวลารุกนั่ง"],
        "diagnosis": ["ความดันโลหิตสูง"],
        "medications": [
            {
                "name": "Amlodipine 5mg",
                "purpose": "ลดความดันโลหิต",
                "dosage_instruction": "รับประทานครั้งละ 1 เม็ด หลังอาหารเช้าทุกวัน ห้ามหยุดยาเอง"
            }
        ],
        "doctor_advice": ["วัดความดันที่บ้านทุกเช้าและจดบันทึกไว้", "ออกกำลังกายเบาๆ เช่น เดินแกว่งแขน"],
        "activity_restriction": ["ระวังการเปลี่ยนอิริยาบถเร็วๆ (ลุก-นั่ง)"],
        "diet_restriction": ["งดอาหารเค็มจัด", "ลดการเติมน้ำปลา ซีอิ๊ว", "งดของหมักดอง"],
        "warning_symptoms": ["ปวดศีรษะรุนแรง", "แขนขาอ่อนแรงซีกใดซีกหนึ่ง", "พูดไม่ชัด", "ปากเบี้ยว"],
        "follow_up_date": "2026-05-15",
        "medical_certificate": None,
        "ipd_admission": {"is_admitted": False}
    },
    {
        "patient_name": "บุญมี ศรีสุข",
        "sex": "ผู้ชาย",
        "hn": "HN-54321",
        "age": 72,
        "visit_datetime": "2026-01-20",
        "hospital_name": "โรงพยาบาลรักษ์คุณตาคุณยาย",
        "department": "แผนกศัลยกรรมกระดูกและข้อ",
        "doctor_name": "นพ. เก่งกาจ กระดูกเหล็ก",
        "vital_signs": {
            "temperature": "36.5 °C",
            "blood_pressure": "130/85 mmHg",
            "heart_rate": "75 bpm"
        },
        "symptoms": ["ปวดเข่าซ้าย", "เวลาเดินมีเสียงก๊อบแก๊บ", "งอเข่าลำบาก"],
        "diagnosis": ["ข้อเข่าเสื่อมระยะเริ่มต้น"],
        "medications": [
            {
                "name": "Ibuprofen 400mg",
                "purpose": "แก้ปวดอักเสบกล้ามเนื้อและข้อ",
                "dosage_instruction": "รับประทานครั้งละ 1 เม็ด หลังอาหารเช้า-เย็น ทันที (ห้ามกินตอนท้องว่าง)"
            },
            {
                "name": "Glucosamine",
                "purpose": "บำรุงข้อเข่า",
                "dosage_instruction": "ชงดื่มวันละ 1 ซอง หลังอาหาร"
            }
        ],
        "doctor_advice": ["บริหารกล้ามเนื้อต้นขาโดยการนั่งเตะขาขึ้นลง", "ใช้ไม้เท้าช่วยเดินถ้าปวดมาก"],
        "activity_restriction": ["งดเดินขึ้นลงบันไดบ่อยๆ", "งดนั่งพับเพียบ นั่งขัดสมาธิ หรือนั่งยองๆ", "งดยกของหนัก"],
        "diet_restriction": ["ควบคุมน้ำหนักไม่ให้เกินเกณฑ์เพื่อลดภาระเข่า"],
        "warning_symptoms": ["เข่าบวม แดง ร้อน", "ปวดจนเดินไม่ลงน้ำหนัก"],
        "follow_up_date": "2026-04-20",
        "medical_certificate": {
            "certificate_date": "2026-01-20",
            "rest_period": "1 วัน"
        },
        "ipd_admission": {"is_admitted": False}
    }
]

visits.insert_many(data)
print(f"✅ Inserted {len(data)} new complete visit records successfully!")