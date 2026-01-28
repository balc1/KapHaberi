import requests
import re
import time
import json
from bs4 import BeautifulSoup
from datetime import datetime

# --- 1. AYARLAR VE OTURUM ---
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://www.kap.org.tr",
})

# --- 2. YARDIMCI FONKSİYONLAR ---
def temizle(metin):
    """HTML etiketlerini temizler."""
    if not metin: return ""
    # <br> ve </p> etiketlerini yeni satır yapalım ki metin yapışmasın
    metin = metin.replace("<br>", "\n").replace("</p>", "\n").replace("<br/>", "\n")
    soup = BeautifulSoup(metin, "html.parser")
    return soup.get_text(separator="\n").strip()

def bildirim_detayi_al(bildirim_id):
    """
    Önce 'disclosureContent', sonra 'Ek Açıklamalar', 
    en son 'Açıklamalar' alanını kontrol eder.
    """
    url = f"https://www.kap.org.tr/tr/Bildirim/{bildirim_id}"
    
    try:
        response = session.get(url)
        if response.status_code == 200:
            html_content = response.text
            
            # ADIM 1: JSON Verisi (En Hızlısı)
            match = re.search(r'"disclosureContent"\s*:\s*"(.*?)"', html_content)
            if match:
                try:
                    ham_veri = match.group(1).encode('utf-8').decode('unicode_escape')
                    temiz = temizle(ham_veri)
                    if len(temiz) > 10: return temiz
                except:
                    pass 

            # ADIM 2: HTML Tablo Tarama (Yedek)
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Aradığımız başlıklar listesi (Sırasıyla dener)
            aranacak_basliklar = ["Ek Açıklamalar", "Açıklamalar", "Açıklama"]
            
            icerik_kutusu = None
            
            for baslik_adi in aranacak_basliklar:
                # Başlığı içeren hücreyi bul (Tam eşleşme veya içinde geçme)
                # re.compile ile esnek arama yapıyoruz
                bulunan_baslik = soup.find("td", string=re.compile(baslik_adi))
                
                if bulunan_baslik:
                    # Başlığın yanındaki hücreyi al
                    icerik_kutusu = bulunan_baslik.find_next("td")
                    if icerik_kutusu:
                        # BULDUK! Döngüyü kır.
                        break
            
            if icerik_kutusu:
                # --- İÇ İÇE DİV SORUNUNU ÇÖZEN KISIM ---
                # separator="\n" parametresi, her div bitişinde bir alt satıra geçer.
                # Böylece kelimeler birbirine yapışmaz.
                metin = icerik_kutusu.get_text(separator="\n", strip=True)
                
                # Gereksiz boşlukları temizle
                metin = re.sub(r'\n+', '\n', metin) # Çoklu boş satırları tek yap
                return metin

            return "" # Hiçbir şey bulunamadı
            
        else:
            return f"Hata: {response.status_code}"
            
    except Exception as e:
        return f"Hata: {e}"

# --- 3. ANA AKIŞ (GÜN SONU RAPORU) ---
def gun_sonu_verisi_topla():
    bugun = datetime.now().strftime("%d.%m.%Y")
    print(f"--- {bugun} Raporu Başlatılıyor ---")

    # A. API'den Listeyi Çek
    list_url = "https://www.kap.org.tr/tr/api/disclosure/list/main"
    payload = {
        "fromDate": bugun,
        "toDate": bugun,
        "disclosureTypes": ["ODA"],
        "fundTypes": ["BYF", "GMF", "GSF", "PFF"],
        "memberTypes": ["IGS", "DDK"],
        "mkkMemberOid": None
    }
    
    headers_json = session.headers.copy()
    headers_json.update({"Content-Type": "application/json"})
    
    resp = session.post(list_url, json=payload, headers=headers_json)
    if resp.status_code != 200:
        print("Liste çekilemedi.")
        return []

    liste_data = resp.json()
    print(f"Toplam {len(liste_data)} bildirim bulundu. Detaylar taranıyor...\n")
    
    rapor_listesi = []

    # B. Her Bildirim İçin Detaya Git
    for i, item in enumerate(liste_data, 1):
        basic = item.get("disclosureBasic", {})
        b_id = basic.get("disclosureIndex")
        sirket = basic.get("companyTitle")
        baslik = basic.get("title")
        ozet_api = basic.get("summary", "") # API'den gelen kısa özet
        
        # Kullanıcıya bilgi ver
        print(f"[{i}] {sirket}: {baslik}")
        
        # Senin fonksiyonunla detayı al
        detay_metni = bildirim_detayi_al(b_id)
        
        # --- C. VERİ BİRLEŞTİRME MANTIĞI ---
        # Eğer detay metni boşsa veya hata mesajıysa -> API Özetini kullan
        # Eğer detay metni varsa -> Onu kullan
        
        if not detay_metni or "Bulunamadı" in detay_metni:
            final_metin = ozet_api
            kaynak = "API Özeti"
        else:
            # Bazen detay metni çok kısa (örn: "Ektedir") olabilir.
            if len(detay_metni) < 20 and ozet_api:
                final_metin = ozet_api
                kaynak = "API Özeti (Detay çok kısaydı)"
            else:
                final_metin = detay_metni
                kaynak = "Web Detayı"

        # Listeye Ekle
        rapor_listesi.append({
            "id": b_id,
            "sirket": sirket,
            "baslik": baslik,
            "icerik": final_metin,
            "kaynak": kaynak
        })
        
        # Sunucuyu yormamak için bekleme
        time.sleep(0.3)

    return rapor_listesi

# --- 4. ÇALIŞTIRMA ---
veriler = gun_sonu_verisi_topla()

print("\n" + "="*50)
print(f"İŞLEM BİTTİ. {len(veriler)} bildirim işlendi.")
print("="*50)

# Örnek Çıktı (JSON Formatında - LLM'e gidecek format)
if veriler:
    # Türkçe karakter sorunu olmasın diye ensure_ascii=False
    json_cikti = json.dumps(veriler, indent=4, ensure_ascii=False)
    print("İLK 2 VERİNİN JSON HALİ (Örnek):")
    print(json_cikti)


# --- 5. VERİYİ DOSYAYA KAYDETME ---
# Veriyi çektikten hemen sonra dosyaya yazıyoruz
dosya_adi = f"kap_verileri_{datetime.now().strftime('%d_%m_%Y')}.json"

with open(dosya_adi, "w", encoding="utf-8") as f:
    json.dump(json_cikti, f, ensure_ascii=False, indent=4)

print(f"Veriler '{dosya_adi}' dosyasına güvenle kaydedildi.")