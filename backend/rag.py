import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url=os.getenv("GROQ_BASE_URL")
)

def format_visit_data(visit):
    
    # 1. จัดการเรื่องข้อมูลยาก่อน
    medications_text = ""
    meds = visit.get("medications", [])
    
    # กันเหนียวเผื่อ meds เป็น None หรือไม่ใช่ List
    if not isinstance(meds, list):
        meds = [meds] if meds else []

    for med in meds:
        if isinstance(med, dict):
            name = med.get("name", "ไม่ระบุชื่อยา")
            dosage = med.get("dosage_instruction", "ไม่ระบุวิธีใช้")
            medications_text += f"- {name} : {dosage}\n"
        else:
            medications_text += f"- {med}\n"

    # ฟังก์ชันช่วยป้องกัน Error ตอนใช้ .join() เผื่อข้อมูลบางอันไม่ใช่ List
    def safe_join(data):
        if not data:
            return "-"
        if isinstance(data, list):
            return ", ".join(str(i) for i in data)
        return str(data)

    # 2. เอาประกอบร่างเป็น summary (เพิ่ม warning_symptoms แล้ว!!)
    # ดึงค่า vital signs ออกมาเตรียมไว้ (ดัก None เผื่อไว้ด้วย)
    vitals = visit.get("vital_signs", {})
    bp = vitals.get("blood_pressure", "-")
    temp = vitals.get("temperature", "-")
    
    summary = f"""
ชื่อผู้ป่วย: {visit.get("patient_name", "ไม่ทราบชื่อ")} (อายุ {visit.get("age", "-")} ปี)
รหัสประจำตัวผู้ป่วย (HN): {visit.get("hn", "-")}
วันที่พบแพทย์: {visit.get("visit_datetime", visit.get("date", "ไม่ระบุวันที่"))}
แพทย์ผู้ตรวจ: {visit.get("doctor_name", "-")} ({visit.get("department", "-")})
สัญญาณชีพ: ความดันโลหิต {bp}, อุณหภูมิร่างกาย {temp}

อาการที่มาพบแพทย์:
{safe_join(visit.get("symptoms", visit.get("symptom")))}

การวินิจฉัยโรค:
{safe_join(visit.get("diagnosis"))}

ยาและวิธีใช้:
{medications_text if medications_text.strip() else "- ไม่มีข้อมูลยา"}

คำแนะนำแพทย์:
{safe_join(visit.get("doctor_advice"))}

ข้อห้ามกิจกรรม:
{safe_join(visit.get("activity_restriction"))}

ข้อห้ามอาหาร:
{safe_join(visit.get("diet_restriction"))}

อาการเตือนที่ต้องรีบมาพบแพทย์ (ฉุกเฉิน):
{safe_join(visit.get("warning_symptoms"))}

วันนัดครั้งถัดไป:
{visit.get("follow_up_date", "ไม่มีการนัด")}
"""

    return summary


def generate_answer(visit_data, question):

    visit_summary = format_visit_data(visit_data)

    # อัปเกรด Prompt ด้วยเทคนิค Few-shot + Chain-of-Thought + Self-Critique
    prompt = f"""
คุณคือ "พยาบาลวิชาชีพ (Telemedicine)" ให้คำปรึกษาผู้ป่วยด้วยความใส่ใจ

=== กฎเหล็กที่ต้องปฏิบัติตาม ===
1. สั้น กระชับ ตรงประเด็น (ตอบไม่เกิน 3-4 บรรทัด)
2. อ้างอิงจาก "ข้อมูลการรักษา" เท่านั้น ห้ามเดาหรือใช้ความรู้ภายนอก
3. หากถามอาการฉุกเฉิน (เช่น ปวดหัวรุนแรง) ที่ตรงกับ "อาการเตือนที่ต้องรีบมาพบแพทย์" ให้แนะนำให้รีบมาโรงพยาบาลทันที
4. หากถามเรื่องที่ "ไม่มี" ในข้อมูล ให้ตอบว่าไม่มีข้อมูลในรอบนี้อย่างสุภาพ
5. ต้องลงท้ายประโยคด้วย "ค่ะ" หรือ "นะคะ" เสมอ ห้ามตอบห้วนๆ
6. สรรพนามผู้ป่วย: ผู้ป่วยมักจะแทนตัวเองว่า "ตา", "ยาย", "ลุง", "ป้า" ดังนั้นหากผู้ป่วยถามเช่น "ความดันตาเท่าไหร่" หรือ "ยายกินยาตัวไหน" ให้เข้าใจว่าหมายถึง "ความดันโลหิตของผู้ป่วย" หรือ "ยาของผู้ป่วย" ห้ามแปลความหมายเป็นอวัยวะ (ลูกตา) เด็ดขาด

=== ตัวอย่างการตอบคำถาม (Few-Shot Examples) ===
คำถาม: ฉันควรหยุดกินยาความดันไหม?
คำตอบ: ตามคำสั่งคุณหมอระบุชัดเจนว่า "ห้ามหยุดยาเอง" ค่ะ แนะนำให้ทานยาตามปกตินะคะ หากกังวลใจควรปรึกษาคุณหมอโดยตรงค่ะ

คำถาม: ตอนนี้รู้สึกปวดท้องมากเลย
คำตอบ: ในประวัติการรักษารอบนี้ไม่มีข้อมูลเรื่องอาการปวดท้องนะคะ หากมีอาการผิดปกติเพิ่มเติม แนะนำให้ติดต่อโรงพยาบาลโดยตรงค่ะ

คำถาม: ปวดศีรษะรุนแรงมากเลยค่ะ
คำตอบ: อาการปวดศีรษะรุนแรงเป็นหนึ่งในอาการเตือนที่ต้องระวังค่ะ แนะนำให้คุณรีบเดินทางมาพบแพทย์ที่โรงพยาบาลทันทีนะคะ

=== ข้อมูลการรักษาของคนไข้รอบนี้ ===
{visit_summary}

=== คำถามจากผู้ป่วย ===
{question}

=== กระบวนการคิดของคุณ (Chain-of-Thought & Self-Critique) ===
1. วิเคราะห์: คำถามนี้ควรอ้างอิงข้อมูลส่วนไหน? (ยา / คำแนะนำ / อาการเตือน / ข้อมูลไม่มี)
2. ร่างคำตอบ: ตอบให้ตรงจุดที่สุด
3. ตรวจทานตัวเอง: คำตอบนี้สั้นพอไหม? มีคำว่า "ค่ะ/นะคะ" หรือยัง? ไม่ได้เดาข้อมูลขึ้นมาเองใช่ไหม?
4. พิมพ์เฉพาะคำตอบสุดท้ายที่ผ่านการตรวจสอบแล้วลงมาด้านล่างนี้เลย

คำตอบ:
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.1,  
        messages=[
            {
                "role": "system",
                "content": "คุณคือพยาบาลระบบ Telemedicine ที่ตอบคำถามอย่างเป็นมืออาชีพ สุภาพ และจัดหน้าเป็นข้อๆ เสมอ"
            },
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

