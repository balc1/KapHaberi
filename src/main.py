import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Proje kök dizinini Python yoluna ekliyoruz ki 'src' klasörünü bulabilsin
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.logger import setup_logger
from src.scraper import KapScraper
from src.analyzer import FinancialLLM
from src.notifier import TelegramNotifier

# Ana loglayıcıyı başlat
logger = setup_logger("Orchestrator")

def main():
    logger.info("=== KAP AI Analiz Botu Başlatılıyor ===")
    
    # Çevresel değişkenleri (.env) yükle
    load_dotenv() 

    try:
        # 1. Modülleri Başlat (Sınıflardan nesneler üretiyoruz)
        scraper = KapScraper()
        analyzer = FinancialLLM()
        notifier = TelegramNotifier()

        # 2. Veri Çekme Aşaması
        veriler = scraper.gunluk_verileri_getir()
        if not veriler:
            logger.warning("İşlenecek veri bulunamadı. Süreç sonlandırılıyor.")
            return

        # 3. Analiz Aşaması
        rapor = analyzer.analyze(veriler)
        if not rapor:
            logger.warning("Rapor oluşturulamadı. Süreç sonlandırılıyor.")
            return

        # 4. Bildirim Aşaması
        bugun_str = datetime.now().strftime("%d.%m.%Y")
        baslik = f"Borsa Gün Sonu Raporu | {bugun_str}"
        
        basari = notifier.send(baslik, rapor)
        
        if basari:
            logger.info("=== Süreç Başarıyla Tamamlandı ===")
        else:
            logger.error("Süreç tamamlandı ancak bildirim gönderilemedi.")

    except Exception as e:
        # Beklenmeyen, sistemi çökerten bir hata olursa yakala ve logla
        logger.critical(f"Sistemde beklenmeyen kritik bir hata oluştu: {e}", exc_info=True)
        # CI/CD (GitHub Actions) sistemine uygulamanın hata ile kapandığını bildir
        sys.exit(1) 

if __name__ == "__main__":
    main()