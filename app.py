from fastapi import FastAPI
from pydantic import BaseModel
from backend.rag import generate_answer
from backend.db import get_visit, get_visit_by_id

app = FastAPI()


class ChatRequest(BaseModel):
    visit_id: str
    question: str


from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h1>Hospital AI</h1>
    <p>Welcome to the system</p>
    <a href="/docs">API Docs</a>
    """

# -------------------------
# GET VISITS
# -------------------------

@app.get("/visits")
def visits():
    visits_data = get_visit()  # ดึงข้อมูลมาจาก db.py
    result = []

    for visit in visits_data:
        # ดักจับเอามาแปลงเป็น text ให้หน้าเว็บเอาไปโชว์บนปุ่มง่ายๆ
        symptoms = visit.get("symptoms", ["ไม่ระบุอาการ"])
        diagnosis = visit.get("diagnosis", ["ไม่ระบุการวินิจฉัย"])
        
        # 1. ก๊อปปี้ข้อมูลทั้งหมดจาก Database มาก่อน (จะได้ข้อมูลยาและคำแนะนำมาครบๆ)
        visit_output = visit.copy()
        
        # 2. เพิ่มคีย์ที่หน้า ui.py ต้องการใช้เข้าไปในก้อนข้อมูลเดิม
        visit_output["visit_id"] = visit["_id"]
        visit_output["date"] = visit.get("visit_datetime", "ไม่ระบุวันที่")
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

