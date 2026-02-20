import logging
import os
from datetime import datetime

# Projenin ana dizinini dinamik olarak bul
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")

def setup_logger(name: str) -> logging.Logger:
    """Proje genelinde kullanılacak standart loglama yapılandırması."""
    
    # Logs klasörü yoksa otomatik oluştur
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Eğer logger daha önce ayarlandıysa (çift log basmasını önlemek için) dön
    if not logger.handlers:
        # Formatter: [2026-02-20 18:30:00] - [Scraper] - [INFO] - Mesaj
        formatter = logging.Formatter('%(asctime)s - %(name)s - [%(levelname)s] - %(message)s')
        
        # 1. Konsol Çıktısı (Ekranda görmek için)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 2. Dosya Çıktısı (Geçmişe dönük hata takibi için logs klasörüne yazar)
        log_file = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y-%m-%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger