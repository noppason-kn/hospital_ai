from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional

# --- 1. สร้าง Schema สำหรับรับข้อมูลจาก Frontend ---
class MedicationSyncRequest(BaseModel):
    visit_id: str
    visit_datetime: str
    medications: List[dict]
    patient_name: Optional[str] = "คุณตา/คุณยาย"

# --- 2. ฟังก์ชันคำนวณวันยาหมด ---
def calculate_min_end_date(visit_date_str, medications):
    start_date = datetime.strptime(visit_date_str, "%Y-%m-%d")
    end_dates = []

    for med in medications:
        # รวมจำนวนเม็ดที่ต้องกินต่อวัน
        daily_dose = (
            med.get("morning", 0) + 
            med.get("afternoon", 0) + 
            med.get("evening", 0) + 
            med.get("before_bed", 0)
        )
        
        if daily_dose > 0:
            total_qty = med.get("total_amount", 0)
            days_duration = total_qty / daily_dose
            end_date = start_date + timedelta(days=days_duration)
            end_dates.append(end_date)
    
    # ส่งคืนวันที่ที่ยาตัวแรกจะหมด (คือวันที่อันตรายที่สุด)
    return min(end_dates) if end_dates else start_date

# --- 3. สร้าง Endpoint /sync-medication ---
@app.post("/sync-medication")
async def sync_medication(data: MedicationSyncRequest):
    try:
        # คำนวณวันยาหมด
        target_end_date = calculate_min_end_date(data.visit_datetime, data.medications)
        end_date_str = target_end_date.strftime("%Y-%m-%d")

        # บันทึกลง MongoDB (Collection ใหม่)
        db.medication_status.update_one(
            {"visit_id": data.visit_id},
            {
                "$set": {
                    "patient_name": data.patient_name,
                    "end_date": end_date_str,
                    "last_sync": datetime.now(),
                    "status": "active"
                }
            },
            upsert=True
        )

        return {"status": "success", "end_date": end_date_str}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))