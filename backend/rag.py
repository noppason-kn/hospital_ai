import os
import re
import mlflow
import mlflow.genai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────
# 🌐 การตั้งค่าการเชื่อมต่อ (Config)
# ─────────────────────────────────────────────────────────
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
mlflow.set_tracking_uri(MLFLOW_URI)
PROMPT_NAME = "health_assistant_prompt"

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url=os.getenv("GROQ_BASE_URL")
)

# ─────────────────────────────────────────────────────────
# 🛡️ Privacy Policy Section (รวมไว้ที่นี่เลย)
# ─────────────────────────────────────────────────────────
def scrub_pii(visit_data: dict) -> dict:
    """
    ฟังก์ชันสำหรับตัดข้อมูลระบุตัวตน (PII) 
    เพื่อให้มั่นใจว่าข้อมูลที่ส่งออกไปนอกระบบ (Cloud LLM) จะไม่มีชื่อจริงคนไข้
    """
    if not visit_data:
        return {}
        
    # สร้างสำเนาข้อมูลเพื่อไม่ให้กระทบข้อมูลต้นฉบับใน DB
    safe_data = visit_data.copy()
    
    # 1. รายชื่อฟิลด์ที่ต้องปกปิดทันที
    pii_fields = ['patient_name', 'id_card', 'phone', 'address', 'citizen_id', 'last_name']
    
    for field in pii_fields:
        if field in safe_data:
            safe_data[field] = "[ข้อมูลส่วนบุคคลถูกปกปิด]"
            
    # 2. ใช้ Regex คัดกรองชื่อในข้อความสรุป (ถ้ามีหลุดมา)
    if 'visit_summary' in safe_data:
        text = str(safe_data['visit_summary'])
        # ลบชื่อที่ตามหลังคำนำหน้าชื่อ (นาย/นาง/นางสาว/เด็กชาย/เด็กหญิง)
        text = re.sub(r'(นาย|นาง|นางสาว|เด็กชาย|เด็กหญิง)\s?([ก-๙]+)\s?([ก-๙]+)', r'\1 [นามสมมติ]', text)
        safe_data['visit_summary'] = text

    return safe_data

# ─────────────────────────────────────────────────────────
# 🧠 RAG & Logic Section
# ─────────────────────────────────────────────────────────
def format_visit_data(visit):
    """เตรียม Context แบบปลอดภัยสำหรับ AI"""
    if not visit: return "ไม่พบข้อมูลการรักษาในระบบ"
    
    # 🟢 STEP 1: เรียกใช้ Privacy Scrubber ภายในไฟล์
    safe_visit = scrub_pii(visit)
    
    sex = safe_visit.get("sex", "ไม่ระบุ")
    display_role = "คุณตา" if "ชาย" in sex else "คุณยาย" if "หญิง" in sex else "ผู้ป่วย"
    
    # ดึงรายการยา
    meds = safe_visit.get("medications", [])
    meds_list = []
    for m in meds:
        if isinstance(m, dict):
            name = m.get('common_name') or m.get('name') or 'ยา'
            inst = m.get('dosage_instruction') or '-'
            meds_list.append(f"- {name}: {inst}")
            
    # รวมข้อมูลสำคัญ (No PII)
    summary = f"""
สถานะผู้ใช้งาน: {display_role}
รายการยาปัจจุบัน:
{chr(10).join(meds_list) if meds_list else 'ไม่มีข้อมูลยา'}
อาการเตือนฉุกเฉิน: {safe_visit.get('warning_symptoms', 'ไม่ระบุ')}
คำแนะนำจากแพทย์: {safe_visit.get('doctor_instructions', 'ไม่ระบุ')}
"""
    return summary.strip()

def generate_answer(visit_data, question, chat_history=None):
    """
    ฟังก์ชันหลักที่รองรับ RAG + Privacy + Chat History ในตัวเดียว
    """
    # 1. เตรียม Context (Retrieved Data + Scrubbed)
    visit_summary = format_visit_data(visit_data)
    
    # 2. เตรียมประวัติการสนทนา (จำได้ 4 ประโยคล่าสุด)
    history_text = ""
    if chat_history:
        for msg in chat_history[-4:]:
            role = "ผู้ป่วย" if msg["role"] == "user" else "พยาบาล"
            history_text += f"{role}: {msg['content']}\n"

    try:
        # 3. ดึง Prompt ล่าสุดจาก MLflow Registry
        prompt_obj = mlflow.genai.load_prompt(f"prompts:/{PROMPT_NAME}/latest")
        raw_template = prompt_obj.template
        
        # 4. แทนที่ตัวแปรใน Template
        final_prompt = raw_template.replace("{{ visit_summary }}", visit_summary).replace("{{ question }}", question)
        
        # ใส่ประวัติแชทถ้าใน Prompt มีรองรับ
        if "{{ chat_history }}" in final_prompt:
            final_prompt = final_prompt.replace("{{ chat_history }}", history_text if history_text else "ไม่มีการสนทนาก่อนหน้า")
        else:
            final_prompt = f"ประวัติการสนทนา:\n{history_text}\n---\n{final_prompt}"

    except Exception as e:
        print(f"⚠️ MLflow Error: {e}")
        # Fallback กรณีระบบ MLflow มีปัญหา
        final_prompt = f"ข้อมูลการรักษา: {visit_summary}\nประวัติแชท: {history_text}\nคำถาม: {question}"

    # 5. ส่งคำขอไปที่ Groq API
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        messages=[
            {"role": "system", "content": "คุณคือพยาบาลอัจฉริยะที่ดูแลผู้สูงอายุอย่างอ่อนโยน ตอบตามข้อมูลที่ให้มาเท่านั้น"},
            {"role": "user", "content": final_prompt}
        ]
    )
    
    return response.choices[0].message.content.strip()