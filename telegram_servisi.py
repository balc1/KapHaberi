import requests
import os
import time

def telegram_gonder(baslik, mesaj_metni):
    """
    Raporu Telegram üzerinden (Kişiye veya Kanala) gönderir.
    Mesaj 4096 karakterden uzunsa otomatik böler.
    """
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID") # Artık buraya @kanal_adi gelecek
    
    if not token or not chat_id:
        print("❌ HATA: Telegram Token veya Chat ID eksik!")
        return False

    # Başlık ve metni birleştir
    tam_mesaj = f"📢 *{baslik}*\n\n{mesaj_metni}"
    
    # Telegram mesaj limiti (Güvenlik payı ile 4000)
    limit = 4000
    parcalar = [tam_mesaj[i:i+limit] for i in range(0, len(tam_mesaj), limit)]
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    basari_durumu = True

    print(f"📨 Mesaj '{chat_id}' hedefine gönderiliyor...")

    for parca in parcalar:
        # Önce Markdown (Kalın/İtalik) ile göndermeyi dene
        payload = {
            "chat_id": chat_id,
            "text": parca,
            "parse_mode": "Markdown" 
        }
        
        try:
            response = requests.post(url, data=payload)
            
            # Eğer Markdown hatası verirse (Örn: metin içinde * veya _ varsa)
            # Düz metin olarak tekrar dene
            if response.status_code != 200:
                print(f"⚠️ Markdown hatası, düz metin deneniyor... (Hata: {response.text})")
                payload.pop("parse_mode") # Formatı iptal et
                retry_response = requests.post(url, data=payload)
                
                if retry_response.status_code == 200:
                    print("✅ Düz metin olarak gönderildi.")
                else:
                    print(f"❌ Gönderim Başarısız: {retry_response.text}")
                    basari_durumu = False
            else:
                print("✅ Mesaj başarıyla iletildi.")

            time.sleep(1) # Spam koruması için bekle
            
        except Exception as e:
            print(f"❌ Bağlantı Hatası: {e}")
            basari_durumu = False
            
    return basari_durumu