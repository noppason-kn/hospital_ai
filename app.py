from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.rag import generate_answer
from db.db import get_visit, get_visit_by_id, db
from datetime import datetime, timedelta
from typing import List, Optional
from backend.line_service import LineNotifier
from backend.helper import format_thai_date, calculate_min_end_date

app = FastAPI()

# --- [แก้จุดที่ 1] สร้าง Instance ไว้ใช้งานใน Backend ---
notifier = LineNotifier()

# Schema สำหรับรับข้อมูล
class ChatRequest(BaseModel):
    visit_id: str
    question: str

class MedicationSyncRequest(BaseModel):
    visit_id: str
    visit_datetime: str
    medications: List[dict]
    patient_name: Optional[str] = "คุณตา/คุณยาย"
    follow_up_date: Optional[str] = "ไม่มีการนัด"


@app.get("/")
def home():
    return {"message": "Hospital AI System is running"}

@app.post("/sync-medication")
async def sync_medication(data: MedicationSyncRequest):
    try:
        today_dt = datetime.now()
        
        # 1. คำนวณวันยาหมด
        target_end_date = calculate_min_end_date(data.visit_datetime, data.medications)
        end_date_thai = format_thai_date(target_end_date)
        
        # 2. บันทึกข้อมูลลง medication_status 
        # เราใช้ visit_id เป็น Key หลัก ดังนั้นถ้ามีหลายโรค/หลาย Visit 
        # ข้อมูลจะถูกแยกเป็นคนละ Record กันโดยอัตโนมัติใน DB
        db.medication_status.update_one(
            {"visit_id": data.visit_id},
            {
                "$set": {
                    "patient_name": data.patient_name,
                    "visit_datetime": data.visit_datetime,
                    "end_date_thai": end_date_thai,
                    "end_date_raw": target_end_date,
                    "follow_up_date": data.follow_up_date,
                    "status": "active",
                    "updated_at": today_dt
                }
            },
            upsert=True
        )

        return {"status": "success", "end_date": end_date_thai}

    except Exception as e:
        print(f"Sync Error: {e}")
        return {"status": "error", "message": str(e)}

# -------------------------
# GET VISITS
# -------------------------
@app.get("/visits")
def visits():
    """ดึงรายการประวัติการรักษาทั้งหมด พร้อมจัดรูปแบบให้หน้าจอแสดงผลง่ายๆ"""
    visits_data = get_visit()
    result = []
    
    for visit in visits_data:
        v = visit.copy()
        
        # 1. จัดการเรื่อง ID ให้เป็น String
        v["visit_id"] = str(visit["_id"])
        
        # 2. จัดรูปแบบวันที่รักษา (ให้หน้าหลักแสดงผลได้เลย)
        raw_date = visit.get("visit_datetime", "-")
        v["date_display"] = format_thai_date(raw_date)
        
        # 3. จัดการเรื่องอาการและการวินิจฉัย (Join List เป็น String)
        def list_to_str(field):
            data = visit.get(field, [])
            if isinstance(data, list):
                return ", ".join(data) if data else "ทั่วไป"
            return str(data) if data else "ทั่วไป"

        v["symptom_display"] = list_to_str("symptoms")
        v["diagnosis_display"] = list_to_str("diagnosis")
        
        # 4. จัดการเรื่องวันนัดหมาย (เพื่อให้ UI ไม่ต้องคำนวณเอง)
        f_date = v.get("follow_up_date")
        f_time = v.get("follow_up_time")
        
        if not f_date or f_date in ["-", "ไม่มีการนัด"]:
            v["next_appointment_clean"] = "ยังไม่มีนัดหมายใหม่ค่ะ ✨"
        else:
            thai_date = format_thai_date(f_date)
            time_text = f" เวลา {f_time} น." if f_time and f_time != "-" else " (ยังไม่ระบุเวลา)"
            v["next_appointment_clean"] = f"{thai_date}{time_text}"
            
        result.append(v)
        
    # เรียงลำดับตามวันที่ล่าสุด (ล่าสุดอยู่บน)
    return sorted(result, key=lambda x: x.get("visit_datetime", ""), reverse=True)

# -------------------------
# CHAT
# -------------------------
@app.post("/chat")
def chat(request: ChatRequest):
    visit = get_visit_by_id(request.visit_id)
    if not visit:
        return {"answer": "ไม่พบข้อมูลการรักษานี้"}
    answer = generate_answer(visit, request.question)
    return {"answer": answer}

