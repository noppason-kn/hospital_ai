import streamlit as st
import requests
from datetime import datetime

API_URL = "http://localhost:8000"

# ตั้งค่าหน้าจอให้เหมาะกับมือถือ
st.set_page_config(page_title="HMS Assistant", layout="centered")

# ---------------------------
# 🎨 HMS UI v2 - Premium Mobile Style
# ---------------------------
st.markdown(
    """
    <style>
    .main .block-container { max-width: 420px; padding-top: 2rem; }
    
    /* สไตล์ Card ใหม่แบบพรีเมียม */
    .visit-card {
        background: white;
        border-radius: 24px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.04);
        border: 1px solid #F0F0F5;
        transition: all 0.3s ease;
    }
    
    .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .card-date { color: #8E8E93; font-size: 13px; display: flex; align-items: center; gap: 4px; }
    
    .card-symptom { 
        color: #1C1C1E; 
        font-size: 22px; 
        font-weight: 700; 
        line-height: 1.2;
        margin-bottom: 15px; 
    }
    
    .doctor-info {
        display: flex;
        align-items: center;
        gap: 8px;
        background: #F8F9FF;
        padding: 8px 12px;
        border-radius: 12px;
        color: #007AFF;
        font-size: 15px;
        font-weight: 500;
        margin-bottom: 15px;
    }

    /* ปุ่มปรึกษา AI แบบใหม่ใน Card */
    .action-area {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-top: 1px solid #F2F2F7;
        padding-top: 15px;
        color: #007AFF;
        font-weight: 600;
        font-size: 15px;
    }

    /* ซ่อนปุ่ม Streamlit ให้แนบไปกับ Card */
    div.stButton > button {
        border: 2px solid #007AFF !important;
        background-color: transparent !important;
        color: #007AFF !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        background-color: #007AFF !important;
        color: white !important;
    }
    
    .logo-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-bottom: 20px;
        padding-top: 10px;
    }
    
    .logo-img {
        width: 100px;
        height: 100px;
        object-fit: contain;
        /* เพิ่มเงาฟุ้งๆ ให้โลโก้ดูพรีเมียม */
        filter: drop-shadow(0 10px 15px rgba(0, 122, 255, 0.2));
        transition: transform 0.3s ease;
    }
    
    .logo-img:hover {
        transform: scale(1.05);
    }

    .brand-name {
        font-size: 28px;
        font-weight: 800;
        color: #1C1C1E;
        margin-top: 10px;
        letter-spacing: -0.5px;
    }
    
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# FUNCTIONS
# ---------------------------
def get_visits():
    try:
        response = requests.get(f"{API_URL}/visits", timeout=5)
        return response.json()
    except:
        return "ไม่สามารถเชื่อมต่อระบบได้ค่ะ"

def send_question(visit_id, question):
    try:
        response = requests.post(f"{API_URL}/chat", json={"visit_id": visit_id, "question": question}, timeout=10)
        return response.json().get("answer", "ขออภัยค่ะ ระบบขัดข้อง")
    except:
        return "ระบบหลังบ้านปิดอยู่ค่ะ"

# ---------------------------
# SESSION STATE
# ---------------------------
if "selected_visit" not in st.session_state: st.session_state.selected_visit = None
if "messages" not in st.session_state: st.session_state.messages = []

# ---------------------------
# PAGE 1: ส่วนแสดงผล Card แบบใหม่
# ---------------------------
# ---------------------------
# PAGE 1: ส่วนแสดงผล Logo และ Card
# ---------------------------
if st.session_state.selected_visit is None:
    # --- ส่วน Logo กลางหน้า ---
    st.markdown(
        """
        <div class="logo-container">
            <img src="https://cdn-icons-png.flaticon.com/512/3063/3063176.png" class="logo-img">
            <div class="brand-name">HMS PORTAL</div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    st.markdown("<p style='text-align: center; color: #8E8E93; margin-top: -10px; margin-bottom: 30px;'>ระบบช่วยจัดการข้อมูลการรักษา AI</p>", unsafe_allow_html=True)
    
    raw_data = get_visits()
    if isinstance(raw_data, list):
        for visit in sorted(raw_data, key=lambda x: x.get("date", ""), reverse=True):
            # วาด UI Card
            st.markdown(f"""
            <div class="visit-card">
                <div class="card-header">
                    <div class="card-date">📅 {visit.get('date', '-')}</div>
                </div>
                <div class="card-symptom">{visit.get('symptom', '-')}</div>
                <div class="doctor-info">
                    🧑‍⚕️ {visit.get('doctor_name', 'ไม่ระบุชื่อหมอ')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # ปุ่มกดที่อยู่ติดกับ Card
            if st.button(f"ปรึกษา AI สำหรับอาการนี้ →", key=f"v_{visit['visit_id']}", use_container_width=True):
                st.session_state.selected_visit = visit
                st.session_state.messages = [] 
                st.rerun()

# ---------------------------
# PAGE 2: หน้าห้องแชท (AI Chat)
# ---------------------------
else:
    visit = st.session_state.selected_visit
    
    # Header สไตล์แอป
    st.markdown(f"""
        <div class="chat-header">
            <div style="font-size: 14px; color: #8E8E93;">กำลังปรึกษาอาการ</div>
            <div style="font-size: 20px; font-weight: bold;">{visit.get('symptom')}</div>
        </div>
    """, unsafe_allow_html=True)

    # ปุ่มย้อนกลับแบบเนียนๆ
    if st.button("❮ ย้อนกลับ", key="back_btn"):
        st.session_state.selected_visit = None
        st.rerun()

    # แสดงข้อควรระวัง (ถ้ามี)
    warn_text = visit.get("warning_symptoms")
    if warn_text:
        st.markdown(f"""
            <div class="danger-box">
                <b>🚨 ข้อควรระวังด่วน!</b><br>
                รีบไป รพ. ทันทีหากมีอาการ: {", ".join(warn_text) if isinstance(warn_text, list) else warn_text}
            </div>
        """, unsafe_allow_html=True)

    # วนลูปแสดงข้อความแชท
    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "content": f"สวัสดีค่ะ มีคำถามเกี่ยวกับการรักษาในวันที่ {visit.get('date')} ไหมคะ?"})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ช่องกรอกคำถาม
    if question := st.chat_input("พิมพ์คำถามของคุณที่นี่..."):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        
        with st.spinner('พยาบาล AI กำลังพิมพ์...'):
            answer = send_question(visit["visit_id"], question)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()
