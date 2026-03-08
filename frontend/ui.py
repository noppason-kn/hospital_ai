import streamlit as st
import requests
from datetime import datetime

API_URL = "http://localhost:8000"

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="HMS Assistant", layout="centered")

# ---------------------------
# 🎨 Senior-First HMS UI (Minimal & High Contrast)
# ---------------------------
st.markdown(
    """
    <style>
        .main .block-container { max-width: 450px; padding: 1rem; }
        
        /* การ์ดแบบใหม่: รวมปุ่มไว้ข้างใน */
        .senior-card {
            background: #FFFFFF;
            border-radius: 28px;
            padding: 25px;
            margin-bottom: 20px;
            border: 2px solid #E9ECEF;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }
        
        /* ตัวหนังสือใหญ่เบิ้ม Contrast สูง */
        .senior-date { color: #6C757D; font-size: 16px; font-weight: 500; }
        .senior-symptom { color: #1C1C1E; font-size: 26px; font-weight: 800; margin: 10px 0; line-height: 1.2; }
        .senior-doctor { color: #007AFF; font-size: 18px; font-weight: 600; margin-bottom: 20px; }

        /* ปุ่มกดที่ดูเป็นปุ่มจริงๆ และใหญ่พอดีนิ้วคนแก่ */
        div.stButton > button {
            background-color: #00B67A !important;
            color: white !important;
            border: none !important;
            border-radius: 30px !important;
            font-size: 50px !important;    /* ตัวอักษร */
            font-weight: 800 !important;
            box-shadow: 0 6px 20px rgba(0,182,122,0.35) !important;
        }
        
        /* ปรับ Logo ให้พอดี */
        .center-logo { text-align: center; margin-bottom: 20px; }
        .center-logo img { width: 120px; }
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

if "selected_visit" not in st.session_state: st.session_state.selected_visit = None
if "messages" not in st.session_state: st.session_state.messages = []

# ---------------------------
# PAGE 1: หน้าหลัก (ท่าแก้โลโก้กลางชัวร์ 100%)
# ---------------------------
if st.session_state.selected_visit is None:
    # --- ท่าบังคับกลางสำหรับมือถือ ---
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
                margin-top: -50px;
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
            # สร้างการ์ดสวยๆ ครอบคลุมข้อมูลและปุ่ม
            st.markdown(f"""
            <div class="senior-card">
                <div class="senior-date">📅 วันที่ไปหาหมอ: {visit.get('date')}</div>
                <div class="senior-symptom">{visit.get('symptom')}</div>
                <div class="senior-doctor">🧑‍⚕️ {visit.get('doctor_name')}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # ปุ่มกดที่วางอยู่ใต้การ์ดทันที (ลดระยะห่างให้เหมือนเป็นชิ้นเดียวกัน)
            st.markdown('<div style="margin-top:-15px; margin-bottom:25px;">', unsafe_allow_html=True)
            if st.button(f"จิ้มตรงนี้เพื่อปรึกษา 👆", key=f"v_{visit['visit_id']}", use_container_width=True):
                st.session_state.selected_visit = visit
                st.session_state.messages = [] 
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("ไม่มีข้อมูลการรักษา")

# --- PAGE 2: Chat ---
else:
    visit = st.session_state.selected_visit
    
    # Green Header
    st.markdown(f"""
        <div class="chat-custom-header">
            <h2 style="margin:0;">🩺 {visit.get('symptom')}</h2>
            <p style="margin:5px 0 0 0; opacity:0.8;">พบแพทย์เมื่อ {visit.get('date')}</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("❮ กลับหน้าหลัก", key="back_btn"):
        st.session_state.selected_visit = None
        st.rerun()

    # Warning Box
    warn_text = visit.get("warning_symptoms")
    if warn_text:
        st.markdown(f'<div class="danger-box">⚠️ ข้อควรระวัง: {", ".join(warn_text) if isinstance(warn_text, list) else warn_text}</div>', unsafe_allow_html=True)

    # Chat Messages
    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "content": "สวัสดีค่ะ มีคำถามเพิ่มเติมเกี่ยวกับการรักษาไหมคะ?"})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if question := st.chat_input("พิมพ์คำถามของคุณที่นี่..."):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        
        with st.spinner('พยาบาล AI กำลังพิมพ์...'):
            answer = send_question(visit["visit_id"], question)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()
