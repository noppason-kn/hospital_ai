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

# ปรับ visit_datetime ให้เป็นช่วงเดือนมีนาคม 2026 ทั้งหมดเพื่อความสดใหม่
data = [
    # ---------------------------------------------------------
    # เคสที่ 1: OPD ตรวจโรคเรื้อรัง (รับยา + มีนัด + มีใบรับรองแพทย์)
    # ---------------------------------------------------------
    {
        "patient_name": "บุญมี ศรีสุข",
        "sex": "ผู้ชาย",
        "hn": "HN-54321",
        "age": 72,
        "visit_id": "V-20260301-001",
        "visit_datetime": "2026-03-01",
        "hospital_name": "โรงพยาบาลรักษ์คุณตาคุณยาย",
        "department": "คลินิกโรคเรื้อรัง (NCDs)",
        "doctor_name": "พญ. วิภาดา ใจเย็น",
        "vital_signs": {"temperature": "36.8 °C", "blood_pressure": "140/90 mmHg", "heart_rate": "80 bpm"},
        "symptoms": ["เวียนศีรษะเล็กน้อย", "ปัสสาวะบ่อยตอนกลางคืน"],
        "diagnosis": ["ความดันโลหิตสูง", "เบาหวานชนิดที่ 2"],
        "medications": [
            {
                "name": "Amlodipine 5mg",
                "common_name": "ยาลดความดัน (เม็ดขาว)",
                "total_amount": 90,
                "morning": 1, "afternoon": 0, "evening": 0, "before_bed": 0,
                "dosage_instruction": "รับประทานครั้งละ 1 เม็ด หลังอาหารเช้าทุกวัน"
            },
            {
                "name": "Metformin 500mg",
                "common_name": "ยาลดน้ำตาลในเลือด (เบาหวาน)",
                "total_amount": 180,
                "morning": 1, "afternoon": 0, "evening": 1, "before_bed": 0,
                "dosage_instruction": "รับประทานครั้งละ 1 เม็ด หลังอาหารเช้าและเย็น"
            }
        ],
        "doctor_advice": ["ลดอาหารเค็มและหวานจัด", "ออกกำลังกายเบาๆ เช่น การเดิน"],
        "activity_restriction": ["ระวังการเปลี่ยนอิริยาบถเร็วๆ ป้องกันหน้ามืด"],
        "diet_restriction": ["งดของหวาน", "งดผลไม้รสหวานจัด เช่น ทุเรียน มะม่วง"],
        "warning_symptoms": ["ปวดศีรษะรุนแรง", "ตาพร่ามัว", "ใจสั่น หน้ามืด"],
        "follow_up_date": "2026-06-01",
        "ipd_admission": {"is_admitted": False},
        # ฟิลด์ใหม่
        "medical_certificate": {"is_issued": True, "rest_days": 1, "note": "มารับการตรวจรักษาโรคเรื้อรังตามนัด"},
        "lab_tests": [],
        "imaging_tests": []
    },

    # ---------------------------------------------------------
    # เคสที่ 2: IPD แอดมิดนอนโรงพยาบาล (ปอดอักเสบ + รับยา + มีนัด + มีใบรับรองแพทย์ให้พักฟื้น)
    # ---------------------------------------------------------
    {
        "patient_name": "บุญมี ศรีสุข",
        "sex": "ผู้ชาย",
        "hn": "HN-54321",
        "age": 72,
        "visit_id": "V-20260310-001",
        "visit_datetime": "2026-03-10",
        "hospital_name": "โรงพยาบาลรักษ์คุณตาคุณยาย",
        "department": "แผนกอายุรกรรม (IPD)",
        "doctor_name": "นพ. สมศักดิ์ รักษาดี",
        "vital_signs": {"temperature": "38.9 °C", "blood_pressure": "110/70 mmHg", "heart_rate": "95 bpm", "oxygen_saturation": "94%"},
        "symptoms": ["ไอมีเสมหะสีเขียว", "หอบเหนื่อย", "ไข้สูง", "อ่อนเพลียมาก"],
        "diagnosis": ["ปอดอักเสบติดเชื้อ (Pneumonia)"],
        "medications": [
            {
                "name": "Amoxicillin/Clavulanate 1000mg",
                "common_name": "ยาฆ่าเชื้อ (ยาปฏิชีวนะ)",
                "total_amount": 14,
                "morning": 1, "afternoon": 0, "evening": 1, "before_bed": 0,
                "dosage_instruction": "รับประทานครั้งละ 1 เม็ด หลังอาหารเช้าและเย็น (ต้องทานให้หมด)"
            },
            {
                "name": "Bromhexine 8mg",
                "common_name": "ยาละลายเสมหะ",
                "total_amount": 30,
                "morning": 1, "afternoon": 1, "evening": 1, "before_bed": 0,
                "dosage_instruction": "รับประทานครั้งละ 1 เม็ด หลังอาหาร เช้า กลางวัน เย็น"
            }
        ],
        "doctor_advice": ["ดื่มน้ำอุ่นมากๆ เพื่อให้เสมหะขับออกง่าย", "ใส่หน้ากากอนามัยตลอดเวลาที่อยู่ร่วมกับผู้อื่น"],
        "activity_restriction": ["งดการทำงานหนักหรือยกของหนัก", "พักผ่อนอยู่บนเตียงเป็นหลักในช่วง 3 วันแรก"],
        "diet_restriction": ["งดน้ำเย็นและของทอดของมัน"],
        "warning_symptoms": ["เหนื่อยหอบมากขึ้น", "ไข้กลับมาสูงเกิน 38 องศา", "ริมฝีปากเขียวคล้ำ"],
        "follow_up_date": "2026-03-24",
        "ipd_admission": {
            "is_admitted": True,
            "admission_date": "2026-03-10",
            "discharge_date": "2026-03-15",
            "ward": "หอผู้ป่วยอายุรกรรมชาย ชั้น 4",
            "bed_number": "402-B"
        },
        # ฟิลด์ใหม่
        "medical_certificate": {"is_issued": True, "rest_days": 7, "note": "ป่วยเป็นปอดอักเสบ สมควรพักฟื้นต่อที่บ้านหลังออกจากโรงพยาบาล"},
        "lab_tests": [
            {"test_name": "CBC (ความสมบูรณ์ของเม็ดเลือด)", "result": "WBC สูง บ่งชี้การติดเชื้อ", "status": "Completed"}
        ],
        "imaging_tests": [
            {"test_name": "Chest X-Ray", "result": "พบฝ้าขาวที่ปอดกลีบล่างขวา", "status": "Completed"}
        ]
    },

    # ---------------------------------------------------------
    # เคสที่ 3: OPD ตรวจติดตาม (ไม่จ่ายยา + หมอให้คุมอาหาร + มีนัดเจาะเลือดแล็บรอบหน้า)
    # ---------------------------------------------------------
    {
        "patient_name": "บุญมี ศรีสุข",
        "sex": "ผู้ชาย",
        "hn": "HN-54321",
        "age": 72,
        "visit_id": "V-20260318-001",
        "visit_datetime": "2026-03-18",
        "hospital_name": "โรงพยาบาลรักษ์คุณตาคุณยาย",
        "department": "แผนกอายุรกรรมทั่วไป",
        "doctor_name": "พญ. วิภาดา ใจเย็น",
        "vital_signs": {"temperature": "36.5 °C", "blood_pressure": "130/80 mmHg", "heart_rate": "78 bpm", "weight": "75 kg"},
        "symptoms": ["ไม่มีอาการผิดปกติ", "มาฟังผลตรวจสุขภาพประจำปี"],
        "diagnosis": ["ภาวะไขมันในเลือดสูง (Hyperlipidemia)"],
        "medications": [], # ไม่จ่ายยา ลองให้คุมอาหารก่อน
        "doctor_advice": ["แพทย์ยังไม่จ่ายยาลดไขมัน แต่ให้ปรับพฤติกรรมการกินอย่างเคร่งครัด 3 เดือน", "เน้นทานปลาและผัก"],
        "activity_restriction": [],
        "diet_restriction": ["งดอาหารที่มีคอเลสเตอรอลสูง เช่น กะทิ ของทอด หมูสามชั้น เครื่องในสัตว์", "ลดแป้งและน้ำตาล"],
        "warning_symptoms": ["เจ็บแน่นหน้าอกร้าวไปกรามหรือแขนซ้าย (อาการโรคหัวใจ)"],
        "follow_up_date": "2026-06-18",
        "ipd_admission": {"is_admitted": False},
        # ฟิลด์ใหม่
        "medical_certificate": {"is_issued": False},
        "lab_tests": [
            {"test_name": "Lipid Profile (เจาะเลือดดูไขมัน)", "result": "Cholesterol 240, LDL 160", "status": "Completed"},
            {"test_name": "Lipid Profile (เจาะเลือดดูไขมัน)", "result": "รอผลตรวจรอบหน้า", "status": "Pending", "appointment_date": "2026-06-18"} # นัดเจาะเลือดรอบหน้า
        ],
        "imaging_tests": []
    },

    # ---------------------------------------------------------
    # เคสที่ 4: ER ฉุกเฉิน (หกล้มที่บ้าน + เอกซเรย์กระดูก + จ่ายยาแก้ปวด)
    # ---------------------------------------------------------
    {
        "patient_name": "บุญมี ศรีสุข",
        "sex": "ผู้ชาย",
        "hn": "HN-54321",
        "age": 72,
        "visit_id": "V-20260322-001",
        "visit_datetime": "2026-03-22",
        "hospital_name": "โรงพยาบาลรักษ์คุณตาคุณยาย",
        "department": "แผนกอุบัติเหตุและฉุกเฉิน (ER)",
        "doctor_name": "นพ. ภานุวัฒน์ กระดูกเหล็ก",
        "vital_signs": {"temperature": "36.7 °C", "blood_pressure": "145/90 mmHg", "heart_rate": "90 bpm"},
        "symptoms": ["ลื่นล้มในห้องน้ำ", "ปวดบวมที่หัวเข่าขวา", "เดินลงน้ำหนักไม่ได้"],
        "diagnosis": ["ฟกช้ำที่ข้อเข่าขวา (Knee Contusion)", "ข้อเข่าเสื่อมระยะเริ่มต้น"],
        "medications": [
            {
                "name": "Diclofenac 400mg",
                "common_name": "ยาแก้ปวดอักเสบกล้ามเนื้อ/ข้อ",
                "total_amount": 20,
                "morning": 1, "afternoon": 0, "evening": 1, "before_bed": 0,
                "dosage_instruction": "รับประทานครั้งละ 1 เม็ด หลังอาหารทันที เช้า-เย็น (หากไม่ปวดสามารถหยุดยาได้)"
            },
            {
                "name": "Diclofenac Gel",
                "common_name": "ยาทาแก้ปวดลดบวม",
                "total_amount": 1,
                "morning": 1, "afternoon": 0, "evening": 1, "before_bed": 1,
                "dosage_instruction": "ทาบางๆ บริเวณที่ปวดบวม วันละ 3-4 ครั้ง"
            }
        ],
        "doctor_advice": ["ประคบเย็นที่เข่าขวาในช่วง 48 ชั่วโมงแรก", "ใช้ไม้เท้าช่วยพยุงเวลาเดิน"],
        "activity_restriction": ["งดเดินขึ้นลงบันได", "ห้ามนั่งพับเพียบ นั่งยอง หรือคุกเข่า"],
        "diet_restriction": [],
        "warning_symptoms": ["เข่าบวมแดงร้อนมากขึ้น", "มีไข้สูง", "ปวดจนทนไม่ไหวแม้กินยา"],
        "follow_up_date": "2026-03-29", # นัดดูอาการอีก 1 สัปดาห์
        "ipd_admission": {"is_admitted": False},
        # ฟิลด์ใหม่
        "medical_certificate": {"is_issued": True, "rest_days": 3, "note": "ได้รับอุบัติเหตุหกล้ม งดเดินเยอะ"},
        "lab_tests": [],
        "imaging_tests": [
            {"test_name": "X-Ray Right Knee", "result": "ไม่พบรอยแตกร้าวของกระดูก (No fracture) พบร่องรอยข้อเข่าเสื่อมเล็กน้อย", "status": "Completed"}
        ]
    },

    # ---------------------------------------------------------
    # เคสที่ 5: คลินิกเฉพาะทางตา (ยาหยอดตา + นัดผ่าตัด)
    # ---------------------------------------------------------
    {
        "patient_name": "บุญมี ศรีสุข",
        "sex": "ผู้ชาย",
        "hn": "HN-54321",
        "age": 72,
        "visit_id": "V-20260328-001",
        "visit_datetime": "2026-03-28",
        "hospital_name": "โรงพยาบาลรักษ์คุณตาคุณยาย",
        "department": "จักษุคลินิก (แผนกตา)",
        "doctor_name": "พญ. ดวงตา สว่างใส",
        "vital_signs": {"temperature": "36.5 °C", "blood_pressure": "125/80 mmHg", "heart_rate": "75 bpm"},
        "symptoms": ["ตามัว มองเห็นภาพซ้อน", "แพ้แสงตอนขับรถกลางคืน"],
        "diagnosis": ["ต้อกระจกตาขวา (Senile Cataract Right Eye)"],
        "medications": [
            {
                "name": "Artificial Tears (น้ำตาเทียม)",
                "common_name": "น้ำตาเทียม",
                "total_amount": 30, # สมมติว่าขวดนึงใช้ได้ 30 วัน
                "morning": 1, "afternoon": 1, "evening": 1, "before_bed": 1,
                "dosage_instruction": "หยอดตาทั้งสองข้าง ครั้งละ 1-2 หยด เมื่อมีอาการตาแห้ง หรือวันละ 4 ครั้ง"
            }
        ],
        "doctor_advice": ["สวมแว่นกันแดดเมื่อออกที่แจ้ง", "หลีกเลี่ยงการขยี้ตา"],
        "activity_restriction": ["งดขับรถเวลากลางคืนเนื่องจากทัศนวิสัยไม่ดี"],
        "diet_restriction": [],
        "warning_symptoms": ["ปวดตารุนแรง", "ตาแดงมาก", "การมองเห็นลดลงอย่างเฉียบพลัน"],
        "follow_up_date": "2026-04-20", # นัดมาเตรียมตัวผ่าตัด
        "ipd_admission": {"is_admitted": False},
        # ฟิลด์ใหม่
        "medical_certificate": {"is_issued": False},
        "lab_tests": [],
        "imaging_tests": [
            {"test_name": "วัดความดันลูกตา (Tonometry)", "result": "ความดันตาปกติทั้งสองข้าง", "status": "Completed"}
        ]
    }
]

# แทรกข้อมูล Visits
inserted_visits = visits.insert_many(data)

# --- ส่วนสำคัญ: สร้างสถานะใน medication_status ให้พร้อมเด้ง LINE ---
for i, visit in enumerate(data):
    v_date = datetime.strptime(visit["visit_datetime"], "%Y-%m-%d")
    
    # 1. คำนวณวันยาหมดจากจำนวนยาจริง
    durations = []
    for med in visit["medications"]:
        daily = med["morning"] + med["afternoon"] + med["evening"] + med["before_bed"]
        if daily > 0:
            durations.append(med["total_amount"] / daily)
    
    # ดักเคสที่ไม่มีการจ่ายยา (เช่น เคสที่ 3) ให้ min_days เป็น 0
    min_days = min(durations) if durations else 0
    end_date_raw = v_date + timedelta(days=min_days)

    # 2. บันทึกลง medication_status เพื่อให้ Prefect ค้นหาเจอ
    # แม้ไม่มีการจ่ายยา ก็บันทึกสถานะไว้เผื่อใช้อ้างอิงการแจ้งเตือนรูปแบบอื่น (เช่น แจ้งเตือนนัดเจาะเลือด)
    med_status.insert_one({
        "visit_id": inserted_visits.inserted_ids[i],
        "patient_name": visit["patient_name"],
        "status": "active" if durations else "inactive", # ถ้าไม่มียาปรับสถานะเป็น inactive
        "end_date_raw": end_date_raw, 
        "follow_up_date": visit["follow_up_date"]
    })

print(f"✅ Inserted {len(data)} visits and prepared active medication status!")
print(f"🚀 ตอนนี้รัน python daily_reminder.py ได้เลย ข้อมูลจะเด้งแน่นอน!")