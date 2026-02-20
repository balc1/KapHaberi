import json
import os
import time
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

def llm_response(veriler_listesi):
    """
    KAP verilerini GÜVENLİ LİMİTLERLE analiz eder.
    Limit aşımı (413 Hatası) olmaması için sıkı önlemler alınmıştır.
    """
    
    # --- KRİTİK AYARLAR ---
    PARCA_BOYUTU = 10   # Güvenli limit
    BEKLEME_SURESI = 65 # Groq limiti için bekleme
    KARAKTER_LIMITI = 350 # Token şişmemesi için kırpma
    
    # --- HATA DÜZELTİCİ (YENİ) ---
    # Eğer veri string olarak geldiyse, listeye çevir
    if isinstance(veriler_listesi, str):
        try:
            print("⚠️ Uyarı: Gelen veri metin formatında, listeye çevriliyor...")
            veriler_listesi = json.loads(veriler_listesi)
        except Exception as e:
            return f"KRİTİK HATA: Veri formatı bozuk, düzeltilemedi. Detay: {e}"

    # Hala liste değilse hata ver
    if not isinstance(veriler_listesi, list):
         return f"KRİTİK HATA: Veri beklenen formatta değil. Gelen tip: {type(veriler_listesi)}"
    
    api_key = os.getenv("GROQ_API_KEY")
    # Test yaparken .env yüklenmediyse diye basit bir kontrol
    if not api_key:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("GROQ_API_KEY")
        except:
            pass
        
    if not api_key:
        return "HATA: GROQ_API_KEY bulunamadı! .env dosyasını kontrol et."

    llm = ChatGroq(
        groq_api_key=api_key,
        model_name="llama-3.3-70b-versatile",
        temperature=0.3,
        max_retries=3
    )

    system_prompt = """
    Sen profesyonel bir Borsa İstanbul (BIST) analisti ve portföy yöneticisisin.
Amacın KAP bildirimlerinden yatırımcı açısından ANLAMLI ve POZİTİF ETKİ POTANSİYELİ olan haberleri ayıklayıp DERLİ TOPLU sunmaktır.

GENEL KURALLAR:
- Parça parça gelen bildirimleri TEK BÜTÜN halinde değerlendir.
- Aynı tür haberleri mutlaka BİRLEŞTİR.
- Gereksiz, rutin, piyasa etkisi olmayan bildirimleri TAMAMEN ELE.
- Yorum ekleme, spekülasyon yapma, sadece haberin yatırımcı açısından neden önemli olduğunu ima et.

SADECE ŞU HABER TÜRLERİNİ KULLAN:
✓ Yeni iş sözleşmeleri / stratejik anlaşmalar  
✓ İhale kazanımı  
✓ Satın alma / birleşme  
✓ Sermaye artırımı (bedelli / bedelsiz)  
✓ Temettü kararları  
✓ Değerleme raporu / varlık değer artışı  

KESİNLİKLE YAZMA:
✗ Devre kesici  
✗ Rutin yönetim kurulu kararları  
✗ Borçlanma aracı ihracı  
✗ Fon işlemleri  
✗ Düzeltme ve tekrar bildirimleri  

FORMAT KURALLARI (ÇOK ÖNEMLİ):

1️⃣ BAŞLIK KULLAN:
Aşağıdaki başlıklardan SADECE gerekli olanları yaz:

🔹 YENİ İŞ VE STRATEJİK ANLAŞMALAR  
🔹 SERMAYE ARTIRIMI VE TEMETTÜ HABERLERİ  
🔹 SATIN ALMA VE DEĞERLEME GELİŞMELERİ  

2️⃣ HER BAŞLIK ALTINDA:
- Tüm ilgili şirketleri TEK PARAGRAF halinde anlat
- Akıcı, okunabilir, yatırımcı dilinde yaz
- Şirketleri parantez içinde KOD ile belirt
- Madde işareti kullanma

3️⃣ YATIRIMCI FİLTRESİ:
- Hisse fiyatına POZİTİF etki yapma potansiyeli olanları ÖNCELİKLENDİR
- Önemsiz büyüklükte veya etkisiz anlaşmaları ELE

4️⃣ HİÇ ÖNEMLİ HABER YOKSA:
SADECE ŞUNU YAZ:
"Bugün yatırımcı açısından anlamlı bir KAP bildirimi bulunmamaktadır."

Özellikle ciroya, kârlılığa veya büyümeye doğrudan katkı sağlayan haberleri önceliklendir.
Sadece "var" diye haber yazma; ETKİSİ YOKSA ELE.

    """

    toplam_veri = len(veriler_listesi)
    print(f"📊 Toplam {toplam_veri} bildirim var. {PARCA_BOYUTU}'arlı paketler halinde işlenecek.")
    
    final_rapor = ""
    
    for i in range(0, toplam_veri, PARCA_BOYUTU):
        grup_ham = veriler_listesi[i : i + PARCA_BOYUTU]
        grup_no = (i // PARCA_BOYUTU) + 1
        toplam_grup = (toplam_veri // PARCA_BOYUTU) + 1 if (toplam_veri % PARCA_BOYUTU) != 0 else (toplam_veri // PARCA_BOYUTU)
        
        print(f"⏳ Paket {grup_no}/{toplam_grup} hazırlanıyor...")
        
        # --- TOKEN OPTİMİZASYONU ---
        grup_metin = ""
        for veri in grup_ham:
            # Veri yapısı kontrolü (Test dosyasında 'icerik' olmayabilir diye)
            if isinstance(veri, str): # Eğer liste içinde string varsa onu da atla
                continue
                
            icerik = veri.get('icerik', '') or veri.get('summary', '') or "İçerik Yok"
            sirket = veri.get('sirket', 'Bilinmiyor')
            baslik = veri.get('baslik', 'Konu Yok')

            temiz_icerik = str(icerik).replace('\n', ' ')[:KARAKTER_LIMITI]
            grup_metin += f"KOD:{sirket} | KONU:{baslik} | DETAY:{temiz_icerik}\n"

        messages = [
            ("system", system_prompt),
            ("human", f"LİSTE:\n{grup_metin}"),
        ]
        
        try:
            print(f"📡 Paket {grup_no} Groq'a gönderiliyor...")
            cevap = llm.invoke(messages).content
            
            if "YOK" not in cevap and len(cevap) > 5:
                final_rapor += cevap + "\n\n"
                print(f"✅ Paket {grup_no}: Veri alındı.")
            else:
                print(f"ℹ️ Paket {grup_no}: Önemli haber yok.")
                
        except Exception as e:
            print(f"⚠️ Paket {grup_no} Hatası: {e}")
        
        # Son grup değilse bekle
        if i + PARCA_BOYUTU < toplam_veri:
            print(f"☕ Kota sıfırlanıyor... {BEKLEME_SURESI} saniye beklenecek.")
            time.sleep(BEKLEME_SURESI)

    if not final_rapor.strip():
        return "Bugün piyasayı etkileyecek kritik bir KAP bildirimi düşmemiştir."
    
    return final_rapor

# ==========================================
# TEST BLOĞU
# ==========================================
if __name__ == "__main__":
    print("\n🔬 TEST MODU BAŞLATILIYOR...")
    
    TEST_DOSYASI = "kap_verileri_28_01_2026.json" 
    
    try:
        # Dosya yoksa otomatik bul
        if not os.path.exists(TEST_DOSYASI):
            json_files = [f for f in os.listdir('.') if f.endswith('.json') and 'kap' in f]
            if json_files:
                TEST_DOSYASI = json_files[0]
                print(f"⚠️ Dosya otomatik seçildi: '{TEST_DOSYASI}'")
            else:
                print("❌ HATA: Test edecek .json dosyası bulunamadı!")
                exit()

        print(f"📂 '{TEST_DOSYASI}' okunuyor...")
        
        with open(TEST_DOSYASI, "r", encoding="utf-8") as f:
            dosya_icerigi = f.read() # Önce hepsini metin olarak oku
            
        # JSON'a çevirmeyi dene
        try:
            test_verisi = json.loads(dosya_icerigi)
            
            # Bazen JSON string içinde string olabilir (Double encoded)
            if isinstance(test_verisi, str):
                print("⚠️ Çift katmanlı JSON tespit edildi, tekrar çözülüyor...")
                test_verisi = json.loads(test_verisi)
                
        except json.JSONDecodeError:
            print("❌ HATA: Dosya geçerli bir JSON değil!")
            exit()
            
        print(f"✅ Dosya başarıyla işlendi. {len(test_verisi)} adet bildirim var.")
        
        # Fonksiyonu çalıştır
        sonuc = llm_response(test_verisi)
        
        print("\n" + "="*40)
        print("🧪 TEST SONUCU (RAPOR):")
        print("="*40)
        print(sonuc)
        print("="*40)
        
    except Exception as e:
        print(f"❌ TEST HATASI DETAYI: {e}")
