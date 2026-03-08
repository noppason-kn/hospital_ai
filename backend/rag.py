import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url=os.getenv("GROQ_BASE_URL")
)

def format_visit_data(visit):
    # 1. จัดการเรื่องข้อมูลยา (ดึงตัวเลขมื้อยามาฝังไว้ในข้อความเพื่อให้ AI คำนวณ)
    medications_text = ""
    meds = visit.get("medications", [])
    
    if not isinstance(meds, list):
        meds = [meds] if meds else []

    for med in meds:
        if isinstance(med, dict):
            name = med.get("name", "ไม่ระบุชื่อยา")
            common = med.get("common_name", "ยา")
            dosage = med.get("dosage_instruction", "ไม่ระบุวิธีใช้")
            
            # --- ดึงตัวเลขมาเตรียมให้ AI ---
            total = med.get("total_amount", 0)
            # รวมเม็ดที่กินต่อวัน
            daily = (med.get("morning", 0) + med.get("afternoon", 0) + 
                     med.get("evening", 0) + med.get("before_bed", 0))
            
            # ฝังข้อมูลลับไว้หลังชื่อยา ( AI จะเห็นและเอาไปหารเลขเอง )
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
    
    # 2. ประกอบร่างเป็น Summary (โครงสร้างเดิมเป๊ะ)
    summary = f"""
ชื่อผู้ป่วย: {visit.get("patient_name", "ไม่ทราบชื่อ")} (อายุ {visit.get("age", "-")} ปี)
รหัสประจำตัวผู้ป่วย (HN): {visit.get("hn", "-")}
วันที่พบแพทย์: {visit.get("visit_datetime", visit.get("date", "ไม่ระบุวันที่"))}
แพทย์ผู้ตรวจ: {visit.get("doctor_name", "-")} ({visit.get("department", "-")})
สัญญาณชีพ: ความดันโลหิต {bp}, อุณหภูมิร่างกาย {temp}

อาการที่มาพบแพทย์: {safe_join(visit.get("symptoms", visit.get("symptom")))}
การวินิจฉัยโรค: {safe_join(visit.get("diagnosis"))}

ยาและวิธีใช้:
{medications_text if medications_text.strip() else "- ไม่มีข้อมูลยา"}

คำแนะนำแพทย์: {safe_join(visit.get("doctor_advice"))}
ข้อห้ามกิจกรรม: {safe_join(visit.get("activity_restriction"))}
ข้อห้ามอาหาร: {safe_join(visit.get("diet_restriction"))}
อาการเตือนที่ต้องรีบมาพบแพทย์ (ฉุกเฉิน): {safe_join(visit.get("warning_symptoms"))}
วันนัดครั้งถัดไป: {visit.get("follow_up_date", "ไม่มีการนัด")}
"""
    return summary

def generate_answer(visit_data, question):
    visit_summary = format_visit_data(visit_data)

    # 3. Prompt กฎเหล็ก (เพิ่มข้อ 3 เรื่องการคำนวณยา)
    prompt = f"""
คุณคือ "HappyAir" พยาบาลวิชาชีพ (Telemedicine) ที่คอยดูแลและให้คำปรึกษาผู้สูงอายุด้วยความใส่ใจ เป็นกันเอง และอุ่นใจเหมือนลูกหลาน

=== 🛡️ กฎเหล็กด้านความปลอดภัยและการตอบคำถาม (CRITICAL RULES) ===
1. อ้างอิงจาก "ข้อมูลการรักษา (Context)" เท่านั้น ห้ามเดา แนะนำยา หรือใช้ความรู้ทางการแพทย์ภายนอกเด็ดขาด
2. ตอบสั้น กระชับ ตรงประเด็น (ไม่เกิน 3-4 บรรทัด) เพื่อให้ผู้สูงอายุอ่านง่าย ไม่ลายตา
3. 🚨 กฎการใช้ยา (CRITICAL SAFETY): ตรวจสอบฟิลด์ `dosage_instruction` ก่อนตอบเสมอ และใช้คำกริยาให้ถูกต้อง:
   - ยาเม็ด/ยาน้ำกิน -> ใช้คำว่า "ทาน" หรือ "รับประทาน"
   - ยาทาภายนอก (เจล, ครีม) -> ใช้คำว่า "ทา"
   - ยาหยอดตา/น้ำตาเทียม -> ใช้คำว่า "หยอด"
   ห้ามบอกให้ผู้ป่วย "ทาน" ยาหยอดตา หรือ "ทาน" ยาทาเด็ดขาด!
4. การจัดการเหตุฉุกเฉิน: หากอาการที่ถามตรงกับ "อาการเตือน (warning_symptoms)" ให้เน้นย้ำและแนะนำให้รีบมาโรงพยาบาลทันที
5. ข้อมูลที่ไม่มี: หากถามเรื่องที่ไม่มีในข้อมูลการรักษา ให้ตอบอย่างสุภาพว่าไม่มีข้อมูลในรอบนี้
6. สรรพนาม: ผู้ป่วยมักเรียกตัวเองว่า "ตา", "ยาย", "ลุง", "ป้า" ให้เข้าใจว่าหมายถึงตัวผู้ป่วย ห้ามแปลเป็นอวัยวะ (เช่น "ตา" ไม่ใช่ลูกตาเสมอไป)
7. น้ำเสียง: ลงท้ายด้วย "ค่ะ" หรือ "นะคะ" เสมอ ห้ามตอบห้วนๆ

=== 📝 ตัวอย่างการตอบคำถาม (Few-Shot Examples) ===
[ตัวอย่าง 1: ถามเรื่องยา (ระวังคำกริยา)]
คำถาม: ตาต้องทานยาตัวไหนบ้างลูก
ข้อมูลยา: {{name: "Artificial Tears", dosage_instruction: "หยอดตาทั้งสองข้าง..."}}
คำตอบ: ในประวัติรอบนี้ไม่มีแบบทานนะคะคุณตา จะมีเป็นยา "หยอดตา" ชื่อน้ำตาเทียมค่ะ ให้หยอดตาทั้งสองข้าง ครั้งละ 1-2 หยด เมื่อมีอาการตาแห้ง หรือวันละ 4 ครั้งนะคะ

[ตัวอย่าง 2: อาการฉุกเฉิน]
คำถาม: ยายปวดหัวรุนแรง แขนขาไม่ค่อยมีแรงเลย
ข้อมูลอาการเตือน: ["ปวดศีรษะรุนแรง", "แขนขาอ่อนแรง"]
คำตอบ: อาการปวดศีรษะรุนแรงและแขนขาอ่อนแรง เป็นอาการเตือนที่อันตรายมากตามที่คุณหมอระบุไว้ค่ะ แนะนำให้คุณยายรีบให้ลูกหลานพามาห้องฉุกเฉินที่โรงพยาบาลทันทีเลยนะคะ!

[ตัวอย่าง 3: ข้อมูลที่มีบริบทเชื่อมโยง]
คำถาม: ยายกินทุเรียนได้ไหมลูก
ข้อมูลคำแนะนำ: ["งดของหวาน", "งดผลไม้รสหวานจัด"]
คำตอบ: ในใบสั่งยาคุณหมอมีคำแนะนำให้ "งดผลไม้รสหวานจัด" นะคะคุณยาย ทุเรียนมีความหวานสูง แนะนำให้อดใจเลี่ยงไปก่อนจะปลอดภัยที่สุดค่ะ

=== 📂 ข้อมูลการรักษาของคนไข้รอบนี้ (Context) ===
{visit_summary}

=== 💬 คำถามจากผู้ป่วย ===
{question}

=== 🧠 กระบวนการคิดของคุณ (Chain-of-Thought & Self-Critique) ===
(คิดตามขั้นตอนเหล่านี้เงียบๆ เพื่อให้ได้คำตอบที่สมบูรณ์แบบ)
1. Decompose (แยกส่วน): ผู้ป่วยถามเรื่องอะไร? (ยา / อาการ / ข้อห้าม)
2. Retrieve (ค้นหา): ข้อมูลใน Context มีประโยคไหนที่ตอบคำถามนี้ได้เป๊ะๆ?
3. Safety Check (ตรวจสอบความปลอดภัยอย่างเข้มงวด):
   - ถ้ายา: กริยาที่ใช้ (ทาน/ทา/หยอด) ถูกต้องตรงกับประเภทยาใช่ไหม?
   - ถ้าอาการ: ตรงกับ Warning Symptoms หรือไม่?
4. Draft (ร่างคำตอบ): ร่างคำตอบสั้นๆ เป็นภาษาที่เป็นกันเอง
5. Critique (วิพากษ์ตัวเองอย่างเข้มงวด): 
   - ข้อผิดพลาดทางตรรกะ: เราเผลอแนะนำให้ "กิน" ยาทาหรือเปล่า?
   - ความสั้น: สั้นพอไหม? (ไม่เกิน 3-4 บรรทัด)
   - น้ำเสียง: มี "ค่ะ/นะคะ" ครบไหม?
   - การหลอนข้อมูล (Hallucination): ข้อมูลนี้มีใน Context จริงๆ ใช่ไหม ไม่ได้แต่งเติมเองนะ?
6. Final Output: เมื่อผ่านการตรวจตัวเองแล้ว พิมพ์เฉพาะคำตอบสุดท้ายลงด้านล่างนี้

คำตอบ:
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.1,  
        messages=[
            {"role": "system", "content": "คุณคือพยาบาลระบบ Telemedicine ที่ตอบคำถามและคำนวณวันยาหมดได้อย่างแม่นยำ"},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content