import requests
import os
import time
from typing import Optional

from src.logger import setup_logger

logger = setup_logger("TelegramNotifier")

class TelegramNotifier:
    """Telegram üzerinden raporları ileten bildirim sınıfı."""
    
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        
        if not self.token or not self.chat_id:
            logger.error("TELEGRAM_TOKEN veya TELEGRAM_CHAT_ID bulunamadı!")
            raise ValueError("Telegram kimlik bilgileri eksik.")
        
        logger.info("TelegramNotifier başlatıldı.")

    def send(self, baslik: str, mesaj_metni: str) -> bool:
        """Mesajı gerektiğinde parçalara bölerek Telegram'a gönderir."""
        tam_mesaj = f"📢 *{baslik}*\n\n{mesaj_metni}"
        limit = 4000
        
        # Mesajı chunk'lara (parçalara) ayır
        parcalar = [tam_mesaj[i:i+limit] for i in range(0, len(tam_mesaj), limit)]
        basari_durumu = True

        logger.info(f"Rapor {len(parcalar)} parça halinde '{self.chat_id}' hedefine gönderiliyor...")

        for parca in parcalar:
            payload = {
                "chat_id": self.chat_id,
                "text": parca,
                "parse_mode": "Markdown" 
            }
            
            try:
                response = requests.post(self.api_url, data=payload, timeout=10)
                
                # Eğer Markdown hatası verirse düz metin (Plain Text) olarak tekrar dene
                if response.status_code != 200:
                    logger.warning(f"Markdown hatası, düz metin deneniyor... Hata: {response.text}")
                    payload.pop("parse_mode")
                    retry_response = requests.post(self.api_url, data=payload, timeout=10)
                    
                    if retry_response.status_code != 200:
                        logger.error(f"Gönderim tamamen başarısız: {retry_response.text}")
                        basari_durumu = False
                
                time.sleep(1) # Spam koruması
                
            except requests.RequestException as e:
                logger.error(f"Telegram ağ bağlantısı hatası: {e}")
                basari_durumu = False
                
        if basari_durumu:
            logger.info("✅ Rapor Telegram'a başarıyla iletildi.")
            
        return basari_durumu