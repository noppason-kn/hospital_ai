import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import requests
from backend.helper import format_thai_date

API_URL = os.getenv("BACKEND_URL", "http://localhost:8080")

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="ผู้ช่วยเตือนสุขภาพ", layout="centered")

# ---------------------------
# 🎨 Senior-First HMS UI (Minimal & High Contrast)
# ---------------------------
st.markdown(
    """
    <style>
        /* =========================================
           1. ตั้งค่าพื้นฐาน
           ========================================= */
        .main .block-container { max-width: 450px; padding: 1rem; }
        .center-logo { text-align: center; margin-bottom: 20px; }
        .center-logo img { width: 120px; }

        .senior-card {
            background: #FFFFFF;
            border-radius: 28px;
            padding: 25px;
            margin-bottom: 5px;
            border: 2px solid #E9ECEF;
            box-shadow: 0 20px 30px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }
        
        .senior-date { color: #6C757D; font-size: 16px; font-weight: 500; }
        .senior-symptom { color: #000000 !important; font-size: 26px; font-weight: 800; margin: 10px 0; line-height: 1.2; }
        .senior-doctor { color: #007AFF; font-size: 18px; font-weight: 600; margin-bottom: 0px; }

        .chat-bubble-ai { background-color: #F0F2F5; color: #1C1C1E; padding: 15px 20px; border-radius: 20px 20px 20px 4px; margin-bottom: 15px; max-width: 85%; font-size: 20px; line-height: 1.4; display: inline-block; }
        .chat-bubble-user { background-color: #00B67A; color: white; padding: 15px 20px; border-radius: 20px 20px 5px 20px; margin-bottom: 15px; max-width: 85%; font-size: 20px; line-height: 1.4; float: right; clear: both; }
        .stChatInputContainer { padding: 10px !important; background-color: #F8F9FA !important; border-top: 2px solid #00B67A !important; }
        .chat-custom-header-clean { background-color: transparent !important; color: #1C1C1E !important; padding: 10px 0; margin-bottom: 10px; border-bottom: 1px solid #E9ECEF; }
        .danger-box-mini { background-color: #FFF3F3; border-left: 6px solid #FF4B4B; color: #911; padding: 15px; border-radius: 12px; font-size: 15px; font-weight: 400; margin: 10px 0; }

        /* =========================================
           🎯 2. กฎการควบคุมปุ่ม (แยกกันชัดเจน ไม่ตีกันแล้ว!)
           ========================================= */

        /* 🟢 ปุ่มหน้า 1: "จิ้มตรงนี้เพื่อปรึกษา" (Primary) */
        div.stButton > button[kind="primary"] {
            background-color: #00B67A !important;
            color: white !important;
            border: none !important;
            border-radius: 30px !important;
            font-size: 40px !important;
            font-weight: 800 !important;
            box-shadow: 0 6px 20px rgba(0,182,122,0.35) !important;
            margin-top: -25px !important;
        }

        /* 🔘 ปุ่มหน้า 2 บนสุด: "ข้อมูลฉบับเต็ม" (Tertiary - โปร่งแสง) */
        div.stButton > button[kind="tertiary"] {
            background-color: transparent !important;
            color: #6C757D !important;
            border: 1px solid #E9ECEF !important;
            border-radius: 12px !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            padding: 2px 10px !important;
            min-height: 32px !important;
            margin-top: -60px !important; /* ดึงขึ้นไปบนสุด */
            margin-bottom: 5px !important;
            box-shadow: none !important;
        }

        /* 🔘 ปุ่มหน้า 2 ตรงกลาง: "กลับหน้าหลัก" (Secondary นอกคอลัมน์ - สีเขียว) */
        div.stButton > button[kind="secondary"] {
            background-color: #00B67A !important; 
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            padding: 2px 10px !important;
            min-height: 32px !important;
            margin-top: -15px !important; /* ดึงให้ชิดปุ่มข้อมูล */
            box-shadow: 0 4px 10px rgba(108,117,125,0.2) !important;
        }
        div.stButton > button[kind="secondary"]:hover {
            background-color: #5A6268 !important;
        }

        /* 🟢 4.3 กลุ่มปุ่มคำถามยอดฮิต (บังคับเขียวแบบเด็ดขาด) */
        .green-button-group div.stButton > button {
            background-color: #00B67A !important; 
            color: white !important;
            border: none !important;
            border-radius: 15px !important;
            font-size: 16px !important;
            font-weight: 600 !important;
            padding: 5px 10px !important;
            min-height: 35px !important;
            margin-top: 0px !important; 
            margin-bottom: -15px !important; /* บีบให้ชิดกัน */
            box-shadow: 0 4px 10px rgba(0,182,122,0.2) !important;
        }

        .green-button-group div.stButton > button:hover {
            background-color: #009A66 !important; 
        }

    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# Logic เหมือนเดิมของนายเป๊ะ
# ---------------------------
def get_visits():
    try:
        response = requests.get(f"{API_URL}/visits", timeout=5)
        return response.json()
    except:
        return "ไม่สามารถเชื่อมต่อได้ค่ะ"

def send_question(visit_id, question):
    try:
        response = requests.post(f"{API_URL}/chat", json={"visit_id": visit_id, "question": question}, timeout=10)
        return response.json().get("answer", "ขออภัยค่ะ ระบบขัดข้อง")
    except:
        return "ระบบหลังบ้านปิดอยู่ค่ะ"
    
@st.dialog("📄 ข้อมูลการรักษา")
def show_full_record(v):
    st.markdown(f"### 🏥 {v.get('hospital_name', 'ไม่ระบุโรงพยาบาล')}")
    st.write(f"**👤 ผู้ป่วย:** {v.get('patient_name', '-')} (อายุ {v.get('age', '-')} ปี)")
    st.write(f"**🏢 แผนก:** {v.get('department', '-')} | **👨‍⚕️ แพทย์:** {v.get('doctor_name', '-')}")
    st.divider()
    
    # 🟢 สร้างฟังก์ชันผู้ช่วย เพื่อเช็กว่าข้อมูลเป็น List หรือ String (กันอาการตัวแตก)
    def format_text(data):
        if isinstance(data, list):
            return ', '.join(data)
        return str(data) if data else '-'

    st.markdown("### 🩺 อาการและการวินิจฉัย")
    # 🟢 เรียกใช้ฟังก์ชันผู้ช่วยแทนการใช้ join ดื้อๆ
    st.write(f"**อาการเบื้องต้น:** {format_text(v.get('symptoms'))}")
    st.write(f"**การวินิจฉัย:** {format_text(v.get('diagnosis'))}")
    
    vs = v.get('vital_signs', {})
    st.write(f"**สัญญาณชีพ:** อุณหภูมิ {vs.get('temperature', '-')} | ความดัน {vs.get('blood_pressure', '-')} | ชีพจร {vs.get('heart_rate', '-')}")
    st.divider()
    
    st.markdown("### 💊 รายการยาที่ได้รับ")
    meds = v.get('medications', [])
    if meds:
        for m in meds:
            st.info(f"**{m.get('name')}** ({m.get('common_name')})\n\n**วิธีใช้:** {m.get('dosage_instruction')}")
    else:
        st.write("✅ ไม่มีการจ่ายยาในรอบนี้")
    st.divider()
    
    st.markdown("### 💡 คำแนะนำจากแพทย์")
    st.write(f"**✅ ข้อปฏิบัติ:** {', '.join(v.get('doctor_advice', ['-']))}")
    st.write(f"**⛔ ข้อห้าม/ระวัง:** {', '.join(v.get('activity_restriction', []) + v.get('diet_restriction', []))}")
    if v.get('warning_symptoms'):
        st.error(f"**🚨 อาการเตือน (รีบพบแพทย์):** {', '.join(v.get('warning_symptoms', []))}")
    
    st.divider()
    appointment_time = v.get('follow_up_time', '-')
    st.markdown(f"📅 **วันนัดถัดไป:** {v.get('follow_up_date', 'ไม่มีนัดหมาย')} เวลา {appointment_time} น.")

if "selected_visit" not in st.session_state: st.session_state.selected_visit = None
if "messages" not in st.session_state: st.session_state.messages = []

# ---------------------------
# PAGE 1: หน้าหลัก (เหมือนเดิม 100%)
# ---------------------------
if st.session_state.selected_visit is None:
    st.markdown(
        """
        <style>
            .force-center {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                width: 100%;
                text-align: center;
                margin-bottom: 5px;
            }
            .force-center img {
                width: 300px;
                height: auto;
                display: block;
                margin-top: -100px;
                margin-bottom: -50px;
            }
        </style>
        <div class="force-center">
            <a href="https://imgbb.com/"><img src="https://i.ibb.co/qYSdssvD/Bold-Minimalist-Creative-Fashion-Logo-Template.png" alt="Bold-Minimalist-Creative-Fashion-Logo-Template" border="0" /></a>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    raw_data = get_visits()
    if isinstance(raw_data, list):
        for visit in sorted(raw_data, key=lambda x: x.get("date", ""), reverse=True):
            raw_date = visit.get('date', '-')
            thai_date_display = format_thai_date(raw_date) 
            
            with st.container():
                st.markdown(f"""
                <div class="senior-card">
                    <div class="senior-date">📅 ประวัติการรักษาเมื่อ: {thai_date_display}</div>
                    <div class="senior-symptom">{visit.get('symptom', 'ไม่ระบุอาการ')}</div>
                    <div class="senior-doctor">🧑‍⚕️: {visit.get('doctor_name', 'ไม่ระบุชื่อหมอ')}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown('<div style="margin-top:-25px; margin-bottom:25px;">', unsafe_allow_html=True)
                # 🟢 บังคับให้เป็นสีเขียวด้วย type="primary" 
                if st.button(f"จิ้มตรงนี้เพื่อปรึกษา 👆", 
                             key=f"v_{visit['visit_id']}", 
                             use_container_width=True, 
                             type="primary"):
                    st.session_state.selected_visit = visit
                    st.session_state.messages = [] 
                    st.rerun()
                    
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning(raw_data)

# ---------------------------
# PAGE 2: Chat
# ---------------------------
else:
    visit = st.session_state.selected_visit
    thai_date_display = format_thai_date(visit.get('date', '-'))

    # 🟢 1. ปุ่ม "ข้อมูลฉบับเต็ม" อยู่บนสุด (โปร่งแสง)
    if st.button("📄 ดูข้อมูลฉบับเต็ม", key="info_btn", use_container_width=True, type="tertiary"):
        show_full_record(visit)
    
    # 🔘 2. ปุ่ม "กลับหน้าหลัก" (ไม่ต้องมี markdown ครอบแล้ว)
    if st.button("❮ กลับหน้าหลัก", key="back_btn", use_container_width=True, type="secondary"):
        st.session_state.selected_visit = None
        st.session_state.messages = []
        st.rerun()

    st.markdown(f"""
        <div class="chat-custom-header-clean">
            <h2 style="margin:0; font-size: 30px; color: #000000; margin-top: 10px;">🩺 {visit.get('symptom')}</h2>
            <p style="margin:5px 0 0 0; color: #6C757D; font-size: 16px;">ประวัติเมื่อ: {thai_date_display}</p>
        </div>
    """, unsafe_allow_html=True)

    warn_text = visit.get("warning_symptoms")
    if warn_text:
        warning_msg = ", ".join(warn_text) if isinstance(warn_text, list) else warn_text
        st.markdown(f'<div class="danger-box-mini">⚠️ หากพบอาการเหล่านี้ <b>{warning_msg}</b> กรุณาพบแพทย์โดยด่วน</div>', unsafe_allow_html=True)

    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "content": "สวัสดีค่ะ มีอะไรสอบถามไหมคะ?"})

    for msg in st.session_state.messages:
        if msg["role"] == "assistant":
            st.markdown(f'<div class="chat-bubble-ai">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble-user">{msg["content"]}</div>', unsafe_allow_html=True)
            st.markdown('<div style="clear:both;"></div>', unsafe_allow_html=True)

    if len(st.session_state.messages) == 1:
        st.markdown('<p style="color: #6C757D; font-size: 16px;">เลือกจิ้มคำถามด้านล่างได้เลยค่ะ 👇</p>', unsafe_allow_html=True)
        col_quick = st.columns(1)[0]
        
        quick_questions = ["ต้องทานยาตัวไหนบ้าง?", "หมอสั่งห้ามทำอะไรบ้าง?", "หยุดยาเองได้ไหม?"]
        
        # 🟢 เปิดกล่อง "บังคับเขียว"
        st.markdown('<div class="green-button-group">', unsafe_allow_html=True) 
        
        for q in quick_questions:
            # 🟢 ไม่ต้องใส่ type="secondary" แล้ว เพราะเราบังคับผ่านกล่องด้านบนแทน
            if col_quick.button(q, key=f"btn_{q}", use_container_width=True): 
                st.session_state.messages.append({"role": "user", "content": q})
                with st.spinner('ผู้ช่วยกำลังพิมพ์...'):
                    answer = send_question(visit["visit_id"], q)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun()
                
        # 🟢 ปิดกล่อง "บังคับเขียว"
        st.markdown('</div>', unsafe_allow_html=True)

    if question := st.chat_input("พิมพ์คำถามของคุณที่นี่..."):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.spinner('ผู้ช่วยกำลังพิมพ์...'):
            answer = send_question(visit["visit_id"], question)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()
        
