import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")

def mail_gonder(konu, icerik_metni):
    try:
        r = resend.Emails.send({
            "from": "BorsaBot <onboarding@resend.dev>", # Kendi domainin yoksa bunu kullanırsın
            "to": os.getenv("RECEIVER_MAIL"),
            "subject": konu,
            "html": f"<p>{icerik_metni.replace(chr(10), '<br>')}</p>" # Satır sonlarını <br> yap
        })
        print("✅ Mail Resend ile gönderildi!")
        return True
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False