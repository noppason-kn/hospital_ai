from datetime import datetime, timedelta

def format_thai_date(date_input):
    """
    ฟังก์ชันเดียวจบ: รองรับทั้ง datetime object และ string วันที่
    จัดการแปลงเป็นวันที่ไทย (พ.ศ.) + เดือนภาษาไทย
    """
    if not date_input or date_input == "ไม่มีการนัด":
        return "ยังไม่มีนัดใหม่ค่ะ"
        
    months = [
        "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]
    
    try:
        # 1. เช็คว่าเป็น datetime object หรือไม่
        if isinstance(date_input, datetime):
            dt = date_input
        else:
            # 2. ถ้าเป็น string ให้พยายาม parse (รองรับทั้ง ISO และ YYYY-MM-DD)
            clean_date = str(date_input).split('T')[0]
            dt = datetime.strptime(clean_date, "%Y-%m-%d")
            
        day = dt.day
        month = months[dt.month - 1]
        year = dt.year + 543
        return f"{day} {month} {year}"
    except Exception as e:
        # ถ้าเกิด Error ให้ส่งค่าเดิมกลับไปกันพัง
        return str(date_input)
    
    
def calculate_min_end_date(visit_date_str, medications):
    try:
        date_part = visit_date_str.split('T')[0]
        start_date = datetime.strptime(date_part, "%Y-%m-%d")
        end_dates = []
        for med in medications:
            daily_dose = (med.get("morning", 0) + med.get("afternoon", 0) + 
                          med.get("evening", 0) + med.get("before_bed", 0))
            if daily_dose > 0:
                total_qty = med.get("total_amount", 0)
                days_duration = total_qty / daily_dose
                end_dates.append(start_date + timedelta(days=days_duration))
        return min(end_dates) if end_dates else start_date
    except Exception as e:
        print(f"Calc Error: {e}")
        return datetime.now()