import streamlit as st
import requests

API_URL = "http://localhost:8000"

# เปลี่ยนเลย์เอาต์เป็น 'centered' เพื่อให้ดูแคบลง คล้ายหน้าจอมือถือมากขึ้นเมื่อเปิดบนคอม
st.set_page_config(page_title="ผู้ช่วยประจำตัว", layout="centered")

# ---------------------------
# CSS STYLE (สไตล์ LINE App)
# ---------------------------
st.markdown(
    """
    <style>
    /* ปรับขนาดฟอนต์ให้ใหญ่ อ่านง่ายเต็มตา */
    html, body, [class*="css"]  {
        font-size: 22px !important;
    }
    
    /* แต่งปุ่มให้เป็นสีเขียวแบบ LINE และปุ่มใหญ่กดง่าย */
    div.stButton > button:first-child {
        background-color: #00B900;
        color: white;
        border-radius: 15px;
        padding: 10px 20px;
        font-size: 22px !important;
        font-weight: bold;
        border: none;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    }
    div.stButton > button:first-child:hover {
        background-color: #008B00;
        color: white;
    }

    /* การ์ด Pinned Message ด้านบนแชท */
    .pinned-message {
        background-color: #E6F2EB;
        border-left: 6px solid #00B900;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    
    .system-event {
        text-align: center;
        margin: 25px 0;
    }
    
    .system-event span {
        background-color: #8c969f;
        color: white;
        font-size: 18px;
        padding: 6px 18px;
        border-radius: 20px;
        display: inline-block;
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
        response = requests.get(f"{API_URL}/visits")
        return response.json()
    except:
        return "ขณะนี้ยังไม่มีประวัติรายการพบแพทย์ค่ะ"

def send_question(visit_id, question):
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"visit_id": visit_id, "question": question}
        )
        return response.json().get("answer", "ขออภัยค่ะ ระบบขัดข้องนิดหน่อย")
    except:
        return "คุณหมอจำลองตอบว่า: ตอนนี้ระบบหลังบ้านยังไม่เชื่อมต่อจ้า"

# ---------------------------
# SESSION STATE MANAGEMENT
# ---------------------------
if "selected_visit" not in st.session_state:
    st.session_state.selected_visit = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------
# PAGE 1: หน้าหลัก
# ---------------------------
if st.session_state.selected_visit is None:
    st.markdown("<h2>🏥 ประวัติการรักษา</h2>", unsafe_allow_html=True)
    st.caption("เลือกรอบที่ไปหาหมอเพื่อดูรายละเอียดได้เลยครับ")

    raw_data = get_visits()
    
    # ตรวจสอบว่าเป็น List หรือไม่ (ถ้าไม่ใช่ เช่น เป็นข้อความ Error ให้กลายเป็น List ว่าง)
    if isinstance(raw_data, list):
        # กรองเอาเฉพาะที่เป็น Dictionary จริงๆ และมีคีย์ที่จำเป็น
        visits = [v for v in raw_data if isinstance(v, dict)]
        # จัดเรียงวันที่
        visits = sorted(visits, key=lambda x: x.get("date") or x.get("visit_datetime") or "", reverse=True)
    else:
        # ถ้าดึงข้อมูลไม่ได้ หรือได้เป็น String มา ให้แสดงแจ้งเตือน
        if isinstance(raw_data, str):
            st.warning(raw_data)
        visits = []

    if not visits and not isinstance(raw_data, str):
        st.write("📭 ไม่พบประวัติการรักษาในระบบค่ะ")

    for visit in visits:
        # ใช้ปุ่มเป็นตัวแทนของการ์ดไปเลย กดปุ๊บเข้าแชทปั๊บ (ผู้สูงอายุจะได้ไม่ต้องเล็งหาปุ่มเล็กๆ)
        button_label = f"📅 {visit.get('date', '-')} | 🤒 {visit.get('symptom', '-')}"
        
        if st.button(button_label, key=f"btn_{visit['visit_id']}", use_container_width=True):
            st.session_state.selected_visit = visit
            st.session_state.messages = [] 
            st.rerun()
        st.write("") # เว้นบรรทัดนิดนึงให้กดง่าย

# ---------------------------
# PAGE 2: หน้าห้องแชท
# ---------------------------
else:
    visit = st.session_state.selected_visit

    # ดึงข้อมูลมาเตรียมไว้
    visit_date = visit.get('date', visit.get('visit_datetime', '-'))
    doc_name = visit.get('doctor_name', visit.get('doctor', 'คุณหมอ'))
    symptoms = visit.get('symptom', visit.get('symptoms', '-'))
    diagnosis = visit.get('diagnosis', '-')
    patient_name = visit.get('patient_name', 'คุณตา/คุณยาย')

    # แปลง List เป็น Text
    if isinstance(symptoms, list): symptoms = ", ".join(symptoms)
    if isinstance(diagnosis, list): diagnosis = ", ".join(diagnosis)

    # ฟังก์ชันสำหรับแสดง Pop-up (Modal)
    @st.dialog("📋 รายละเอียดการรักษาฉบับเต็ม")
    def show_full_info_dialog(data):
        st.markdown(
            f"""
            <p style="font-size: 24px; color: #1F2937; line-height: 1.6;">
                <b>📅 วันที่:</b> {visit_date}<br><br>
                <b>👨‍⚕️ แพทย์ผู้ตรวจ:</b><br>{doc_name}<br><br>
                <b>🤒 อาการที่แจ้ง:</b><br>{symptoms}<br><br>
                <b>🩺 สรุปผลวินิจฉัย:</b><br>{diagnosis}
            </p>
            <hr>
            <p style="font-size: 16px; color: #6B7280;">ข้อมูลดิบในระบบ (Raw Data):</p>
            """, 
            unsafe_allow_html=True
        )
        st.json(data)
        
        st.markdown("<br>", unsafe_allow_html=True)
        # ปุ่มปิดใหญ่ๆ เด่นๆ สีแดง
        if st.button("❌ กดตรงนี้เพื่อปิดหน้าต่าง", use_container_width=True):
            st.rerun()

    # ==========================================
    # ส่วนหัว: ปุ่มย้อนกลับ (ซ้าย) และ ปุ่มดูข้อมูล (ขวา)
    # ==========================================
    col1, col_space, col2 = st.columns([3, 2, 5])
    
    with col1:
        if st.button("⬅️ ย้อนกลับ", use_container_width=True):
            st.session_state.selected_visit = None
            st.rerun()

    with col2:
        if st.button("🔎 ดูข้อมูลฉบับเต็ม", use_container_width=True):
            show_full_info_dialog(visit)
        
        button_label = "❌ ปิดข้อมูล" if st.session_state.show_full_info else "📋 ข้อมูลฉบับเต็ม"
        if st.button(button_label, use_container_width=True):
            st.session_state.show_full_info = not st.session_state.show_full_info
            st.rerun()

    # ==========================================
    # ส่วนแสดงข้อมูลฉบับเต็ม (โชว์เมื่อกดปุ่มขวาบน)
    # ==========================================
    if st.session_state.show_full_info:
        st.markdown(
            f"""
            <div style="background-color: #F4F6F8; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 2px solid #D1D5DB;">
                <h4 style="margin-top: 0; color: #1F2937;">🗂️ ข้อมูลการรักษา (สำหรับลูกหลาน/แพทย์)</h4>
                <p style="font-size: 20px; color: #374151; line-height: 1.6;">
                    <b>📅 วันที่ไปหาหมอ:</b> {visit_date}<br>
                    <b>🤒 อาการเบื้องต้น:</b> {symptoms}<br>
                    <b>🩺 การวินิจฉัยโรค:</b> {diagnosis}<br>
                    <b>👨‍⚕️ แพทย์ผู้ตรวจ:</b> {doc_name}
                </p>
                <hr style="border-color: #D1D5DB;">
                <p style="font-size: 16px; color: #6B7280; margin-bottom: 10px;">ข้อมูลดิบทั้งหมดจากระบบ (Raw Data):</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.json(visit) # โชว์ข้อมูลดิบต่อท้าย
        st.markdown("---")

    # ==========================================
    # 1. กล่องข้อความแจ้งเตือน (System Event) กลางจอ
    # ==========================================
    st.markdown(
        f"""
        <style>
        .system-event {{
            text-align: center;
            margin: 10px 0px 30px 0px;
        }}
        .system-event span {{
            background-color: #8c969f;
            color: white;
            font-size: 16px;
            padding: 8px 20px;
            border-radius: 20px;
            display: inline-block;
            box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
        }}
        .danger-box {{
            background-color: #FFF0F0;
            border-left: 8px solid #FF3B30;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 25px;
            box-shadow: 0px 4px 10px rgba(255, 59, 48, 0.2);
        }}
        .danger-title {{
            color: #FF3B30;
            font-size: 26px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .danger-text {{
            font-size: 22px;
            color: #333;
            line-height: 1.5;
        }}
        </style>
        <div class="system-event">
            <span>📅 {visit_date} | 👨‍⚕️ {doc_name} | 🤒 {symptoms} | 🩺 {diagnosis}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 🚨 2. กล่องเตือนภัย "โป้งๆ เท่าฝาบ้าน" (ถ้ามี)
    warning_symp = visit.get("warning_symptoms", [])
    restrictions = visit.get("activity_restriction", []) + visit.get("diet_restriction", [])
    
    if warning_symp or restrictions:
        danger_content = ""
        if warning_symp:
            warn_text = ", ".join(warning_symp) if isinstance(warning_symp, list) else warning_symp
            danger_content += f"<li><b>อาการฉุกเฉิน (ต้องรีบไป รพ.):</b> {warn_text}</li>"
        if restrictions:
            rest_text = ", ".join(restrictions) if isinstance(restrictions, list) else restrictions
            danger_content += f"<li><b>ข้อห้ามเด็ดขาด:</b> {rest_text}</li>"

        st.markdown(
            f"""
            <div class="danger-box">
                <div class="danger-title">🚨 ข้อควรระวังด่วน!</div>
                <ul class="danger-text">
                    {danger_content}
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ==========================================
    # 3. พื้นที่แชท
    # ==========================================
    if len(st.session_state.messages) == 0:
        greeting_msg = f"สวัสดีค่ะ คุณ{patient_name} ต้องการสอบถามข้อมูลใดเกี่ยวกับการรักษาวันนี้คะ"
        st.session_state.messages.append({"role": "assistant", "content": greeting_msg})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(f"<p style='font-size: 22px;'>{msg['content']}</p>", unsafe_allow_html=True)

    question = st.chat_input("พิมพ์คำถามที่สงสัยตรงนี้ได้เลยค่ะ...")

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(f"<p style='font-size: 22px;'>{question}</p>", unsafe_allow_html=True)

        answer = send_question(visit["visit_id"], question)
        
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(f"<p style='font-size: 22px;'>{answer}</p>", unsafe_allow_html=True)
            
