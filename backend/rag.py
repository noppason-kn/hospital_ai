import os
import mlflow
import mlflow.genai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ตั้งค่า URI เชื่อมต่อ MLflow ภายใน Docker
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
mlflow.set_tracking_uri(MLFLOW_URI)
PROMPT_NAME = "health_assistant_prompt"

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url=os.getenv("GROQ_BASE_URL")
)

def format_visit_data(visit):
    if not visit: return "ไม่พบข้อมูล"
    sex = visit.get("sex", "ไม่ระบุ")
    display_role = "คุณตา" if "ชาย" in sex else "คุณยาย" if "หญิง" in sex else "ผู้ป่วย"
    meds = visit.get("medications", [])
    meds_list = []
    for m in meds:
        if isinstance(m, dict):
            meds_list.append(f"- {m.get('name')}: {m.get('dosage_instruction')}")
    return f"สถานะ: {display_role}\nรายการยา:\n" + "\n".join(meds_list)

def generate_answer(visit_data, question):
    """ฟังก์ชันที่ใช้ตอบคำถาม โดยรองรับ Prompt แบบปีกกาคู่ {{ }} """
    visit_summary = format_visit_data(visit_data)
    
    try:
        # 1. ดึง Prompt จาก MLflow
        prompt_obj = mlflow.genai.load_prompt(f"prompts:/{PROMPT_NAME}/latest")
        raw_template = prompt_obj.template
        
        # 2. 🟢 แก้ไข: ใช้ .replace แทน .format เพื่อให้รองรับ {{ }} ที่นายเซฟไว้
        final_prompt = raw_template.replace("{{ visit_summary }}", visit_summary).replace("{{ question }}", question)
        print("✅ ใช้ Prompt จาก MLflow สำเร็จ")
    except Exception as e:
        # Fallback กรณี MLflow ยังไม่มีข้อมูล
        print(f"⚠️ MLflow Error: {e}")
        final_prompt = f"ข้อมูลคนไข้: {visit_summary}\nคำถาม: {question}\nกรุณาตอบเป็นภาษาไทยอย่างสุภาพ:"

    # 3. ยิงไปที่ Groq API
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        messages=[
            {"role": "system", "content": "คุณคือพยาบาลผู้ดูแลผู้สูงอายุ ตอบคำถามตาม Context เท่านั้น"},
            {"role": "user", "content": final_prompt}
        ]
    )
    return response.choices[0].message.content.strip()
