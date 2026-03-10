import os
import requests
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env
load_dotenv()

class LineNotifier:
    def __init__(self):
        # 🟢 ดึง Long-lived Token แบบถาวรมาใช้เลย ไม่ต้องสร้างใหม่แล้ว!
        self.access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        self.user_id = os.getenv("LINE_USER_ID")  # ID ทดสอบ (รหัสตัว U)

    def send_push(self, message, target_user_id=None):
        """
        ฟังก์ชันหลักสำหรับส่งข้อความ Push Notification
        """
        if not self.access_token:
            print("❌ [ERROR] ไม่พบ LINE_CHANNEL_ACCESS_TOKEN ในไฟล์ .env")
            return False

        # ถ้าไม่ระบุ ID ปลายทาง ให้ใช้ค่าเริ่มต้นจาก .env
        dest_id = target_user_id if target_user_id else self.user_id
        
        url = "https://api.line.me/v2/bot/message/push"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
        
        payload = {
            "to": dest_id,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                print(f"✅ [LINE SUCCESS] แจ้งเตือนส่งสำเร็จ!")
                return True
            else:
                print(f"❌ [LINE FAILED] Push Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ [ERROR] ระบบส่ง LINE ขัดข้อง: {e}")
            return False

# --- สำหรับทดสอบการทำงาน ---
if __name__ == "__main__":
    notifier = LineNotifier()
    # ลองส่งข้อความทดสอบ
    notifier.send_push("🔔 ระบบดูแลสุขภาพ: ทดสอบการแจ้งเตือนกินยาและนัดหมายด้วย Token ถาวรครับ")
