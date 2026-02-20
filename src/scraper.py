import requests
import re
import time
from typing import List, Dict
from bs4 import BeautifulSoup
from datetime import datetime

# Kendi yazdığımız profesyonel logger'ı içeri aktarıyoruz
from src.logger import setup_logger

logger = setup_logger("KapScraper")

class KapScraper:
    """KAP (Kamuyu Aydınlatma Platformu) üzerinden günlük bildirimleri çeken sınıf."""
    
    def __init__(self):
        # Sınıf başlatıldığında gerekli ayarları (Session) hazırla
        self.base_url = "https://www.kap.org.tr/tr/api/disclosure/list/main"
        self.detail_url_template = "https://www.kap.org.tr/tr/Bildirim/{id}"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Origin": "https://www.kap.org.tr",
        })
        logger.info("KapScraper modülü başlatıldı.")

    def _temizle(self, metin: str) -> str:
        """HTML etiketlerini temizler. Baştaki '_' işareti bunun 'private' bir fonksiyon olduğunu belirtir."""
        if not metin:
            return ""
        metin = metin.replace("<br>", "\n").replace("</p>", "\n").replace("<br/>", "\n")
        soup = BeautifulSoup(metin, "html.parser")
        return soup.get_text(separator="\n", strip=True)

    def _bildirim_detayi_al(self, bildirim_id: int) -> str:
        """Belirli bir bildirimin HTML detay sayfasını kazır."""
        url = self.detail_url_template.format(id=bildirim_id)
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Bildirim detayı alınamadı. HTTP {response.status_code} - ID: {bildirim_id}")
                return ""

            html_content = response.text
            
            # YÖNTEM 1: JSON Regex
            match = re.search(r'"disclosureContent"\s*:\s*"(.*?)"', html_content)
            if match:
                try:
                    ham_veri = match.group(1).encode('utf-8').decode('unicode_escape')
                    temiz = self._temizle(ham_veri)
                    if len(temiz) > 10: 
                        return temiz
                except Exception as e:
                    logger.debug(f"JSON Decode hatası (ID: {bildirim_id}): {e}")

            # YÖNTEM 2: BeautifulSoup HTML
            soup = BeautifulSoup(html_content, "html.parser")
            aranacak_basliklar = ["Ek Açıklamalar", "Açıklamalar", "Açıklama"]
            
            for baslik_adi in aranacak_basliklar:
                baslik = soup.find("td", string=re.compile(baslik_adi))
                if baslik:
                    icerik_kutusu = baslik.find_next("td")
                    if icerik_kutusu:
                        metin = icerik_kutusu.get_text(separator="\n", strip=True)
                        return re.sub(r'\n+', '\n', metin)

            return ""
        except requests.RequestException as e:
            logger.error(f"Bildirim {bildirim_id} için ağ hatası: {e}")
            return ""

    def gunluk_verileri_getir(self) -> List[Dict]:
        """Günün KAP bildirimlerini ana API'den çeker ve detaylarıyla birleştirir."""
        bugun = datetime.now().strftime("%d.%m.%Y")
        logger.info(f"{bugun} tarihi için KAP verileri toplanıyor...")

        payload = {
            "fromDate": bugun,
            "toDate": bugun,
            "disclosureTypes": ["ODA"],
            "fundTypes": ["BYF", "GMF", "GSF", "PFF"],
            "memberTypes": ["IGS", "DDK"],
            "mkkMemberOid": None
        }
        
        headers_json = self.session.headers.copy()
        headers_json.update({"Content-Type": "application/json"})
        
        try:
            resp = self.session.post(self.base_url, json=payload, headers=headers_json, timeout=15)
            resp.raise_for_status() # HTTP hatası varsa exception fırlatır
            liste_data = resp.json()
        except Exception as e:
            logger.error(f"KAP API bağlantı hatası: {e}")
            return []

        logger.info(f"Toplam {len(liste_data)} bildirim bulundu. Detaylar işleniyor...")
        rapor_listesi = []

        for i, item in enumerate(liste_data, 1):
            basic = item.get("disclosureBasic", {})
            b_id = basic.get("disclosureIndex")
            
            detay_metni = self._bildirim_detayi_al(b_id)
            ozet_api = basic.get("summary", "")
            
            final_metin = detay_metni if (detay_metni and len(detay_metni) >= 20) else ozet_api

            rapor_listesi.append({
                "sirket": basic.get("companyTitle", "Bilinmiyor"),
                "baslik": basic.get("title", "Konu Yok"),
                "icerik": final_metin
            })
            
            time.sleep(0.3) # Sunucuyu yormamak için limit koruması
            
            if i % 20 == 0:
                logger.info(f"İşlenen bildirim: {i}/{len(liste_data)}")

        logger.info(f"Veri çekme başarıyla tamamlandı. ({len(rapor_listesi)} kayıt)")
        return rapor_listesi

# Test etmek için (Sadece bu dosya çalıştırıldığında tetiklenir)
if __name__ == "__main__":
    scraper = KapScraper()
    veriler = scraper.gunluk_verileri_getir()
    print(f"\nÖrnek Çıktı: {veriler[:1] if veriler else 'Veri bulunamadı.'}")