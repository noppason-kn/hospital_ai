import jwt
import time
import requests
import json
import os
from dotenv import load_dotenv
from jwt.algorithms import RSAAlgorithm

# โหลดค่าจากไฟล์ .env
load_dotenv()

class LineNotifier:
    def __init__(self):
        self.channel_id = os.getenv("LINE_CHANNEL_ID")
        self.kid = os.getenv("LINE_KID")
        self.user_id = os.getenv("LINE_USER_ID")  # ID ทดสอบ (รหัสตัว U)
        self.private_key_path = "backend/private_key.json"

    def _get_access_token(self):
        """
        ขั้นตอนการแลกเปลี่ยน Key Pair เป็น Channel Access Token v2.1 (OAuth 2.0)
        """
        try:
            # 1. อ่าน Private Key
            with open(self.private_key_path, "r") as f:
                private_key_jwk = json.load(f)

            # 2. สร้าง JWT Header และ Payload ตามมาตรฐาน RFC 7519
            now = int(time.time())
            header = {
                "alg": "RS256",
                "typ": "JWT",
                "kid": self.kid
            }
            payload = {
                "iss": self.channel_id,
                "sub": self.channel_id,
                "aud": "https://api.line.me/",
                "exp": now + (60 * 30),      # JWT มีอายุ 30 นาที
                "token_exp": 60 * 60 * 24 * 30 # Access Token ที่ขอได้จะมีอายุ 30 วัน
            }

            # 3. เซ็นชื่อด้วย Private Key (RS256)
            key = RSAAlgorithm.from_jwk(json.dumps(private_key_jwk))
            assertion = jwt.encode(payload, key, algorithm="RS256", headers=header)

            # 4. ส่งไปขอ Token จาก LINE API
            url = "https://api.line.me/oauth2/v2.1/token"
            data = {
                "grant_type": "client_credentials",
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": assertion
            }
            
            response = requests.post(url, data=data)
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                print(f"❌ Token Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error during Token generation: {e}")
            return None

    def send_push(self, message, target_user_id=None):
        """
        ฟังก์ชันหลักสำหรับส่งข้อความ Push Notification
        """
        token = self._get_access_token()
        if not token:
            return False

        # ถ้าไม่ระบุ ID ปลายทาง ให้ใช้ค่าเริ่มต้นจาก .env
        dest_id = target_user_id if target_user_id else self.user_id
        
        url = "https://api.line.me/v2/bot/message/push"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
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

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"✅ แจ้งเตือนส่งสำเร็จ: {message}")
            return True
        else:
            print(f"❌ Push Error: {response.text}")
            return False

# --- สำหรับทดสอบการทำงาน ---
if __name__ == "__main__":
    notifier = LineNotifier()
    # ลองส่งข้อความทดสอบ
    notifier.send_push("🔔 ระบบดูแลสุขภาพ: ทดสอบการแจ้งเตือนกินยาและนัดหมายครับ")
    
