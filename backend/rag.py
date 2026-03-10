import os
import sys
import time
import json
import mlflow
import mlflow.genai
import dagshub
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────
# 1. การตั้งค่า DagsHub & MLflow (เชื่อมต่อ Cloud)
# ─────────────────────────────────────────────────────────
REPO_OWNER = "noppason-kn"
REPO_NAME = "my-first-repo"
PROMPT_NAME = "health_assistant_prompt"

print(f"📡 Connecting to DagsHub: {REPO_OWNER}/{REPO_NAME}")

try:
    # ยืนยันตัวตนกับ DagsHub
    dagshub.init(repo_owner=REPO_OWNER, repo_name=REPO_NAME, mlflow=True)
    
    # ตั้งค่า URI ให้ชี้ไปที่ DagsHub
    DAGSHUB_MLFLOW_URI = f"https://dagshub.com/{REPO_OWNER}/{REPO_NAME}.mlflow"
    mlflow.set_tracking_uri(DAGSHUB_MLFLOW_URI)
    
    # ตั้งค่า Experiment
    mlflow.set_experiment("HealthAssistant_Prompt_Evolution")
    print("✅ Connected to DagsHub MLflow Server.")
except Exception as e:
    print(f"❌ DagsHub Connection Failed: {e}")
    sys.exit(1)

client = OpenAI(
    api_key=os.getenv("GROQ_FOR_MLFLOW"),
    base_url=os.getenv("GROQ_BASE_URL")
)

# ─────────────────────────────────────────────────────────
# 2. Helper Functions (UI & Groq API)
# ─────────────────────────────────────────────────────────
def call_llm(prompt: str, temperature: float = 0.1) -> str:
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=temperature,
            messages=[
                {"role": "system", "content": "คุณคือผู้เชี่ยวชาญด้านสุขภาพและ Prompt Engineering"},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"⚠️ Error calling LLM: {e}")
        time.sleep(5)
        return "ERROR"

def print_title(text: str, level: int = 1):
    if level == 1:
        print(f"\n{'━' * 62}\n 🔷 {text}\n{'━' * 62}")
    elif level == 2:
        print(f"\n ── {text} {'─' * max(1, 50 - len(text))}")
    else:
        print(f"\n ▸ {text}")

def print_box(title: str, content: str, emoji: str = "📌"):
    width = 78
    inner_width = width - 4
    print(f"\n ┌{'─' * (width - 2)}┐")
    print(f" │ {emoji} {title:<{inner_width - 2}}│")
    print(f" ├{'─' * (width - 2)}┤")
    for line in content.split("\n"):
        line = line.rstrip()
        while len(line) > inner_width:
            cut_point = line[:inner_width].rfind(" ")
            if cut_point <= 0: cut_point = inner_width
            print(f" │ {line[:cut_point]:<{inner_width}} │")
            line = line[cut_point:].lstrip()
        print(f" │ {line:<{inner_width}} │")
    print(f" └{'─' * (width - 2)}┘")

# ─────────────────────────────────────────────────────────
# 3. Dataset (ข้อสอบ)
# ─────────────────────────────────────────────────────────
TEST_CONTEXT = """
ชื่อผู้ป่วย: บุญมี ศรีสุข (อายุ 72 ปี)
วันที่พบแพทย์: 2026-03-28
แพทย์ผู้ตรวจ: พญ. ดวงตา สว่างใส (จักษุคลินิก (แผนกตา))
อาการที่มาพบแพทย์: ตามัว มองเห็นภาพซ้อน, แพ้แสงตอนขับรถกลางคืน
ยาและวิธีใช้:
- น้ำตาเทียม (Artificial Tears) : หยอดตาทั้งสองข้าง ครั้งละ 1-2 หยด เมื่อมีอาการตาแห้ง หรือวันละ 4 ครั้ง [คงเหลือ: 30 เม็ด, ทานวันละ: 4 เม็ด]
คำแนะนำแพทย์: สวมแว่นกันแดดเมื่อออกที่แจ้ง, หลีกเลี่ยงการขยี้ตา
ข้อห้ามกิจกรรม: งดขับรถเวลากลางคืนเนื่องจากทัศนวิสัยไม่ดี
อาการเตือน (ฉุกเฉิน): ปวดตารุนแรง, ตาแดงมาก, การมองเห็นลดลงอย่างเฉียบพลัน
วันนัดครั้งถัดไป: 2026-04-20
"""

TEST_DATASET = [
    {"question": "ตาต้องกินน้ำตาเทียมกี่เม็ดลูก?", "expected_must": ["หยอด"], "expected_must_not": ["กิน", "รับประทาน", "เม็ด"]},
    {"question": "น้ำตาเทียมใช้วันละกี่ครั้งจ๊ะ", "expected_must": ["4"], "expected_must_not": []},
    {"question": "ยายปวดตารุนแรงมากเลย ทำไงดี", "expected_must": ["โรงพยาบาล"], "expected_must_not": []},
    {"question": "ยายกินยาลดความดันได้ไหม", "expected_must": ["ไม่มี"], "expected_must_not": ["กินได้"]},
    {"question": "เดี๋ยวตาขับรถออกไปซื้อของแป๊บนึงนะ", "expected_must": ["งด"], "expected_must_not": ["ได้ค่ะ"]}
]

INITIAL_PROMPT = """คุณคือผู้ช่วยเตือนสุขภาพที่คอยดูแลและให้คำปรึกษาผู้สูงอายุด้วยความใส่ใจ เป็นกันเอง และอุ่นใจเหมือนลูกหลาน

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
6. สรรพนามและน้ำเสียง: ผู้ป่วยมักเรียกตัวเองว่า "ตา", "ยาย", "ลุง", "ป้า" ให้เข้าใจว่าหมายถึงตัวผู้ป่วย ห้ามแปลเป็นอวัยวะ ลงท้ายด้วย "ค่ะ" หรือ "นะคะ" เสมอ

=== 📂 ข้อมูลการรักษา (Context) ===
{{ visit_summary }}

=== 💬 คำถามจากผู้ป่วย ===
{{ question }}

คำตอบ:"""

# ─────────────────────────────────────────────────────────
# 4. Evaluation & Optimization Logic
# ─────────────────────────────────────────────────────────
def evaluate_prompt(template: str, iteration_label: str):
    correct_count = 0
    results = []
    print_title(f"ประเมิน: {iteration_label}", 2)

    for idx, item in enumerate(TEST_DATASET, start=1):
        filled_prompt = template.replace("{{ visit_summary }}", TEST_CONTEXT).replace("{{ question }}", item["question"])
        raw_answer = call_llm(filled_prompt, temperature=0.1).strip()
        
        final_answer = raw_answer.split("คำตอบ:")[-1].strip() if "คำตอบ:" in raw_answer else raw_answer
        
        is_pass = True
        reason = ""
        for word in item["expected_must"]:
            if word not in final_answer: is_pass = False; reason += f"ขาด '{word}' "
        for word in item["expected_must_not"]:
            if word in final_answer: is_pass = False; reason += f"หลุดคำว่า '{word}' "

        if is_pass: correct_count += 1
        results.append({"q": item["question"], "a": final_answer, "pass": is_pass, "reason": reason})

        status = "✅" if is_pass else "❌"
        print(f"      {status} Q{idx} | ถาม: {item['question'][:30]}...")

    accuracy = (correct_count / len(TEST_DATASET)) * 100
    print_box(f"ผลลัพธ์ {iteration_label}", f"Accuracy: {accuracy:.1f}% ({correct_count}/{len(TEST_DATASET)})", "🎯")
    return accuracy, results

def reflect_and_improve(current_template, accuracy, results):
    wrong_summary = json.dumps([r for r in results if not r["pass"]], ensure_ascii=False, indent=2)
    
    reflection_prompt = f"""คุณคือ Prompt Engineer ระดับโลก ภารกิจของคุณคือแก้ไข Prompt ให้ฉลาดขึ้น

## Prompt ปัจจุบัน:
```text
{current_template}
```

## ผลการทดสอบ (Accuracy {accuracy}%):
{wrong_summary}

## ภารกิจ:
1. วิเคราะห์จุดผิดพลาด ห้ามให้ AI บอกว่า "ทาน" ยาหยอดตาเด็ดขาด
2. สร้าง Prompt ใหม่ที่ดักทางข้อผิดพลาดเหล่านี้ โดยต้องคงโครงสร้างเดิมไว้
3. ครอบ Prompt ใหม่ด้วย [START] และ [END] เท่านั้น

⚠️ กฎเหล็ก: ต้องมี {{{{ visit_summary }}}} และ {{{{ question }}}} เหมือนเดิม!
"""
    print_title("🧠 AI กำลังวิเคราะห์และปรับปรุง Prompt...", 3)
    new_raw = call_llm(reflection_prompt, temperature=0.5)
    
    if "[START]" in new_raw and "[END]" in new_raw:
        return new_raw.split("[START]")[1].split("[END]")[0].strip()
    return current_template

# ─────────────────────────────────────────────────────────
# 5. Main Loop
# ─────────────────────────────────────────────────────────
def main():
    print_title("เริ่มระบบพัฒนา Prompt อัตโนมัติ (DagsHub Tracking)")
    current_prompt = INITIAL_PROMPT
    
    # 🟢 ตัวแปรสำหรับจำ "แชมป์เปี้ยน" ของรอบการเทรนนี้
    best_acc = -1.0
    best_version = None
    
    # เริ่ม Run ใหญ่บน MLflow
    with mlflow.start_run(run_name=f"Optimization_{time.strftime('%Y%m%d_%H%M')}"):
        mlflow.set_tag("developer", REPO_OWNER)
        
        for i in range(1, 4): # รัน 3 รอบ
            iteration_label = f"Iteration {i}"
            
            # 1. วัดผล
            acc, details = evaluate_prompt(current_prompt, iteration_label)
            
            # 2. บันทึกทุกอย่างลง MLflow (Metric + Prompt Text + Results)
            mlflow.log_metric("accuracy", acc, step=i)
            mlflow.log_text(current_prompt, f"prompts/iter_{i}_prompt.txt")
            mlflow.log_dict(details, f"results/iter_{i}_details.json")
            
            # 3. จดทะเบียน Prompt ลง Model Registry
            # 🟢 แก้ไข: ใช้ "Acc: {acc}%" เพื่อให้ rag.py ของนายดึงไปใช้ได้แบบเป๊ะๆ
            reg = mlflow.genai.register_prompt(
                name=PROMPT_NAME,
                template=current_prompt,
                commit_message=f"Iteration {i} | Acc: {acc}%"
            )
            print(f"📦 จดทะเบียน Version: {reg.version} สำเร็จ!")
            mlflow.set_tag(f"iter_{i}_version", reg.version)

            # 🟢 เช็กและบันทึกแชมป์เปี้ยน
            if acc > best_acc:
                best_acc = acc
                best_version = reg.version

            if acc >= 100:
                print_title("🏆 บรรลุเป้าหมาย 100% แล้ว!", 1)
                break
            
            # 4. พัฒนาต่อ (Reflection)
            if i < 3:
                current_prompt = reflect_and_improve(current_prompt, acc, details)
                time.sleep(2)

        # 🟢 บันทึกข้อมูลของแชมป์ลงใน Run ใหญ่
        mlflow.set_tag("best_prompt_version", best_version)
        mlflow.log_metric("best_accuracy", best_acc)

    # 🟢 ปรินต์สรุปตอนจบให้นายดูง่ายๆ ว่าตัวไหนเก่งสุด
    print_title("สรุปผลลัพธ์การฝึกฝน")
    print_box("แชมป์เปี้ยน (Best Version)", f"🏆 Version ที่ดีที่สุด: v{best_version}\n🎯 Accuracy: {best_acc}%\n(ระบบ RAG จะดึงตัวนี้ไปใช้อัตโนมัติ)", "🌟")

    print_title("เสร็จสิ้น! เช็กผลได้ที่เว็บ DagsHub แถบ MLflow")
    print(f"🔗 URL: https://dagshub.com/{REPO_OWNER}/{REPO_NAME}/experiments")

if __name__ == "__main__":
    main()