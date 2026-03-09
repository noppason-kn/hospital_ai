import os
import mlflow
import mlflow.genai
from openai import OpenAI
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env
load_dotenv()

# 1. ตั้งค่า URI (ปรับพอร์ตเป็น 5001 หากคุณทำตามขั้นตอนหลบพอร์ตชนใน GCP ก่อนหน้า)
# หากคุณใช้พอร์ต 5000 เดิมใน Docker ก็ไม่ต้องแก้ไขตรงนี้ครับ
DEFAULT_MLFLOW_URI = "http://mlflow:5000" if os.getenv("DOCKER_ENV") else "http://127.0.0.1:5000"
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", DEFAULT_MLFLOW_URI)
PROMPT_NAME = "health_assistant_prompt"

mlflow.set_tracking_uri(MLFLOW_URI)

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url=os.getenv("GROQ_BASE_URL")
)

# ข้อมูลสำหรับทดสอบความแม่นยำ (ประหยัด Token)
eval_data = [
    {
        "visit_summary": "ผู้ป่วย: คุณตาบุญมี, ยา: ยาหยอดตา (หยอดตาข้างซ้าย 1 หยด วันละ 4 ครั้ง), ยาแก้ปวด (ทานครั้งละ 1 เม็ด หลังอาหาร)",
        "question": "ยาขวดเล็กๆ นี่ต้องกินยังไงนะ?",
        "ground_truth": "ห้ามรับประทานเด็ดขาด! ใช้สำหรับหยอดตาเท่านั้น"
    }
]

def evaluate_current_prompt(template):
    """ฟังก์ชันทดสอบความแม่นยำแบบประหยัด Token"""
    correct_count = 0
    for item in eval_data:
        # 🟢 แก้ไขจุดนี้: ใช้ .replace แทน .format เพราะใน Prompt ใช้ {{ }} 
        # เพื่อป้องกัน Python สับสนกับโครงสร้าง Dictionary
        prompt = template.replace("{{ visit_summary }}", item["visit_summary"]).replace("{{ question }}", item["question"])
        
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            answer = response.choices[0].message.content.strip()
            # เช็คความถูกต้องเบื้องต้น
            is_correct = any(word in answer for word in ["หยอด", "ห้ามรับประทาน", "ห้ามกิน"])
            if is_correct: correct_count += 1
        except Exception as e:
            print(f"⚠️ Error ระหว่างทดสอบ AI: {e}")
            
    return (correct_count / len(eval_data)) * 100

def run_quick_registration():
    """บันทึก Best Prompt ลง MLflow ทันที"""
    
    best_known_prompt = """คุณคือผู้ช่วยเตือนสุขภาพที่คอยดูแลและให้คำปรึกษาผู้สูงอายุด้วยความใส่ใจ เป็นกันเอง และอุ่นใจเหมือนลูกหลาน

=== 🛡️ กฎเหล็กด้านความปลอดภัยและการตอบคำถาม (CRITICAL RULES) ===
1. อ้างอิงจาก "ข้อมูลการรักษา (Context)" เท่านั้น ห้ามเดา แนะนำยา หรือใช้ความรู้ทางการแพทย์ภายนอกเด็ดขาด
2. ตอบสั้น กระชับ ตรงประเด็น (ไม่เกิน 3-4 บรรทัด) เพื่อให้ผู้สูงอายุอ่านง่าย
3. 🚨 กฎการใช้ยา (CRITICAL SAFETY): ตรวจสอบฟิลด์ `dosage_instruction` ก่อนตอบเสมอ และใช้คำกริยาให้ถูกต้อง:
   - ยาเม็ด/ยาน้ำกิน -> ใช้คำว่า "ทาน" หรือ "รับประทาน"
   - ยาทาภายนอก -> ใช้คำว่า "ทา"
   - ยาหยอดตา/น้ำตาเทียม -> ใช้คำว่า "หยอด"
   ห้ามบอกให้ผู้ป่วย "ทาน" ยาหยอดตาเด็ดขาด!
4. การจัดการเหตุฉุกเฉิน: หากอาการตรงกับ "อาการเตือน (warning_symptoms)" ให้เน้นย้ำไปโรงพยาบาลทันที
5. ข้อมูลที่ไม่มี: หากถามเรื่องที่ไม่มี ให้ตอบอย่างสุภาพว่าไม่มีข้อมูลในรอบนี้
6. สรรพนามและน้ำเสียง: ใช้คำว่า "คุณตา", "คุณยาย", "นะคะ", "ค่ะ" ลงท้ายเสมอ

=== 📝 ตัวอย่างการตอบคำถาม (Few-Shot Examples) ===
คำถาม: ตาต้องทานยาตัวไหนบ้างลูก
ข้อมูลยา: {{name: "Artificial Tears", dosage_instruction: "หยอดตาทั้งสองข้าง..."}}
คำตอบ: ไม่มีแบบทานนะคะคุณตา จะมีเป็นยา "หยอดตา" ชื่อน้ำตาเทียมค่ะ ให้หยอดตาทั้งสองข้าง ครั้งละ 1-2 หยด หรือวันละ 4 ครั้งนะคะ

=== 📂 ข้อมูลการรักษา (Context) ===
{{ visit_summary }}

=== 💬 คำถามจากผู้ป่วย ===
{{ question }}

=== 🧠 Chain-of-Thought ===
(คิดเงียบๆ ก่อนตอบ: ตรวจสอบความถูกต้องของคำกริยา และเช็กอาการฉุกเฉิน ห้ามใช้คำว่ากินกับยาหยอดตา)
คำตอบ:"""

    print(f"🚀 กำลังเชื่อมต่อกับ MLflow ที่: {MLFLOW_URI}")
    
    try:
        with mlflow.start_run(run_name="Manual_Best_Prompt_Registration"):
            # รันประเมินแค่รอบเดียว
            accuracy = evaluate_current_prompt(best_known_prompt)
            print(f"📊 Accuracy Check: {accuracy}%")
            
            mlflow.log_metric("accuracy", accuracy)
            
            # 💾 บันทึกลง Registry
            mlflow.genai.log_prompt(
                prompt=best_known_prompt,
                base_model="llama-3.3-70b-versatile",
                name=PROMPT_NAME
            )
            print(f"✨ บันทึก Prompt ลง MLflow Registry เรียบร้อย: {PROMPT_NAME}")
    except Exception as e:
        print(f"❌ ไม่สามารถเชื่อมต่อ MLflow ได้: {e}")
        print("คำแนะนำ: ตรวจสอบว่า Docker 'mlflow_server' รันอยู่และเข้าหน้าเว็บ 5000/5001 ได้ปกติ")

if __name__ == "__main__":
    run_quick_registration()
