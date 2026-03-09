import os
import mlflow
import mlflow.genai
from openai import OpenAI
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env
load_dotenv()

# ตั้งค่า Client สำหรับเชื่อมต่อกับ Groq API
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url=os.getenv("GROQ_BASE_URL")
)

# 1. การตั้งค่าเชื่อมต่อกับ MLflow Server
# ตรวจสอบให้แน่ใจว่า MLflow server กำลังรันอยู่ที่พอร์ต 5000
mlflow.set_tracking_uri("http://127.0.0.1:5000")

# 2. โหลด Prompt ที่ดีที่สุดจาก MLflow Registry
# เปลี่ยนเลข '11' เป็นเลขเวอร์ชันล่าสุดที่คุณรันได้ Accuracy 100%
try:
    best_prompt = mlflow.genai.load_prompt('prompts:/health_assistant_prompt/11')
except Exception as e:
    print(f"⚠️ ไม่สามารถโหลด Prompt จาก MLflow ได้: {e}")
    # กรณีโหลดไม่ได้ ให้ใช้ Template สำรอง (Fallback)
    best_prompt = None

def format_visit_data(visit):
    """
    ฟังก์ชันสำหรับแปลงข้อมูลจาก Database เป็นข้อความสรุป (Summary)
    พร้อมทำการลบข้อมูลส่วนบุคคล (Privacy Scrubbing)
    """
    
    # --- มาตรการความเป็นส่วนตัว (Privacy Scrubbing) ---
    # 1. เปลี่ยนชื่อจริงเป็นสรรพนามตามเพศ
    sex = visit.get("sex", "ไม่ระบุ")
    if "ชาย" in sex or sex == "ผู้ชาย":
        display_role = "คุณตา"
    elif "หญิง" in sex or sex == "ผู้หญิง":
        display_role = "คุณยาย"
    else:
        display_role = "ผู้ป่วย"

    # 2. จัดการข้อมูลยา (คำนวณวันยาหมดเบื้องต้นให้ AI)
    medications_text = ""
    meds = visit.get("medications", [])
    if not isinstance(meds, list):
        meds = [meds] if meds else []

    for med in meds:
        if isinstance(med, dict):
            name = med.get("name", "ไม่ระบุชื่อยา")
            common = med.get("common_name", "ยา")
            dosage = med.get("dosage_instruction", "ไม่ระบุวิธีใช้")
            
            # ดึงตัวเลขมาฝังเพื่อให้ AI ช่วยคำนวณวันยาหมด
            total = med.get("total_amount", 0)
            daily = (med.get("morning", 0) + med.get("afternoon", 0) + 
                     med.get("evening", 0) + med.get("before_bed", 0))
            
            medications_text += f"- {common} ({name}) : {dosage} [คงเหลือ: {total} เม็ด, ทานวันละ: {daily} เม็ด]\n"
        else:
            medications_text += f"- {med}\n"

    def safe_join(data):
        if not data: return "-"
        if isinstance(data, list): return ", ".join(str(i) for i in data)
        return str(data)

    vitals = visit.get("vital_signs", {})
    bp = vitals.get("blood_pressure", "-")
    temp = vitals.get("temperature", "-")
    
    # 3. ประกอบร่างเป็นสรุปข้อมูล (ตัด HN และชื่อแพทย์ออกเพื่อความเป็นส่วนตัว)
    summary = f"""
สถานะผู้ป่วย: {display_role} (อายุ {visit.get("age", "-")} ปี)
วันที่พบแพทย์: {visit.get("visit_datetime", visit.get("date", "ไม่ระบุวันที่"))}
แผนกที่เข้ารับการรักษา: {visit.get("department", "-")}
สัญญาณชีพพื้นฐาน: ความดันโลหิต {bp}, อุณหภูมิร่างกาย {temp}

อาการที่มาพบแพทย์: {safe_join(visit.get("symptoms", visit.get("symptom")))}
การวินิจฉัยของแพทย์: {safe_join(visit.get("diagnosis"))}

รายการยาและวิธีใช้:
{medications_text if medications_text.strip() else "- ไม่มีข้อมูลยาในรอบนี้"}

คำแนะนำเพิ่มเติมจากแพทย์: {safe_join(visit.get("doctor_advice"))}
ข้อห้าม/ข้อควรระวังเรื่องกิจกรรม: {safe_join(visit.get("activity_restriction"))}
ข้อห้าม/ข้อควรระวังเรื่องอาหาร: {safe_join(visit.get("diet_restriction"))}
อาการเตือนฉุกเฉินที่ต้องรีบมาโรงพยาบาล: {safe_join(visit.get("warning_symptoms"))}
วันนัดหมายครั้งถัดไป: {visit.get("follow_up_date", "ไม่มีการนัดหมาย")}
"""
    return summary

def generate_answer(visit_data, question):
    """
    ฟังก์ชันหลักในการสร้างคำตอบโดยใช้ RAG และ Prompt จาก MLflow
    """
    # เตรียมข้อมูล Context ที่ถูก Scrub ข้อมูลส่วนตัวแล้ว
    visit_summary = format_visit_data(visit_data)

    # ตรวจสอบว่าโหลด Prompt จาก MLflow สำเร็จหรือไม่
    if best_prompt:
        # แทนค่าลงในเทมเพลตที่ดึงมาจาก MLflow
        final_prompt = best_prompt.format(visit_summary=visit_summary, question=question)
    else:
        # กรณีฉุกเฉินถ้า MLflow ล่ม ให้ใช้ String เปล่าๆ หรือ Template พื้นฐาน
        final_prompt = f"Context: {visit_summary}\nQuestion: {question}"

    # เรียกใช้งาน LLM ผ่าน Groq
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.1,  # ตั้งค่าต่ำเพื่อให้ตอบตามข้อเท็จจริง
        messages=[
            {"role": "system", "content": "คุณคือผู้ช่วยสุขภาพระบบ Telemedicine ที่มีความเชี่ยวชาญและสุภาพ"},
            {"role": "user", "content": final_prompt}
        ]
    )
    
    raw_answer = response.choices[0].message.content.strip()
    
    # การล้างข้อมูลคำตอบ (Post-processing)
    # หาก AI มีการเขียนกระบวนการคิด (CoT) ให้ตัดออกแสดงเฉพาะส่วนคำตอบสุดท้าย
    if "คำตอบ:" in raw_answer:
        final_answer = raw_answer.split("คำตอบ:")[-1].strip()
    elif "Final Output:" in raw_answer:
        final_answer = raw_answer.split("Final Output:")[-1].strip()
    else:
        final_answer = raw_answer
        
    return final_answer
