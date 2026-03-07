from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.rag import generate_answer
from db.db import get_visit, get_visit_by_id, db
from datetime import datetime, timedelta
from typing import List, Optional
from backend.line_service import LineNotifier

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

# --- [แก้จุดที่ 2] Helper แปลงวันที่เป็นภาษาไทยแบบบ้านๆ ---
def get_thai_month(date_obj):
    months = [
        "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]
    day = date_obj.day
    month = months[date_obj.month - 1]
    year = date_obj.year + 543 # แปลงเป็น พ.ศ.
    return f"{day} {month} {year}"

def calculate_min_end_date(visit_date_str, medications):
    try:
        date_part = visit_date_str.split('T')[0]
        start_date = datetime.strptime(date_part, "%Y-%m-%d")
        end_dates = []
        for med in medications:
            daily_dose = (med.get("morning", 0) + med.get("afternoon", 0) + 
                          med.get("evening", 0) + med.get("before_bed", 0))
            if daily_dose > 0:
                total_qty = med.get("total_amount", 0)
                days_duration = total_qty / daily_dose
                end_dates.append(start_date + timedelta(days=days_duration))
        return min(end_dates) if end_dates else start_date
    except Exception as e:
        print(f"Calc Error: {e}")
        return datetime.now()

# -------------------------
# ROUTES
# -------------------------

@app.get("/")
def home():
    return {"message": "Hospital AI System is running"}

@app.post("/sync-medication")
async def sync_medication(data: MedicationSyncRequest):
    try:
        today_dt = datetime.now()
        
        # 1. คำนวณวันยาหมด
        target_end_date = calculate_min_end_date(data.visit_datetime, data.medications)
        end_date_thai = get_thai_month(target_end_date)
        
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

        # ไม่ต้อง notifier.send_push แล้ว! 
        # เก็บไว้ให้ Scheduler (Prefect) ทำงานตอน 9 โมงเช้าทีเดียว
        
        return {"status": "success", "end_date": end_date_thai}

    except Exception as e:
        print(f"Sync Error: {e}")
        return {"status": "error", "message": str(e)}

# -------------------------
# GET VISITS
# -------------------------
@app.get("/visits")
def visits():
    visits_data = get_visit()
    result = []
    for visit in visits_data:
        visit_output = visit.copy()
        visit_output["visit_id"] = str(visit["_id"])
        visit_output["date"] = visit.get("visit_datetime", "ไม่ระบุวันที่")
        
        symptoms = visit.get("symptoms", ["ไม่ระบุอาการ"])
        diagnosis = visit.get("diagnosis", ["ไม่ระบุการวินิจฉัย"])
        visit_output["symptom"] = ", ".join(symptoms) if isinstance(symptoms, list) else str(symptoms)
        visit_output["diagnosis"] = ", ".join(diagnosis) if isinstance(diagnosis, list) else str(diagnosis)
        
        result.append(visit_output)
    return result

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

