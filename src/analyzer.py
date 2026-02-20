import json
import os
import time
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

def llm_response(veriler_listesi):
    """
    İKİ AŞAMALI ANALİZ:
    1. AŞAMA (MADENCİ): Verileri parçalar halinde tarar, sadece önemli ham bilgiyi çıkarır.
    2. AŞAMA (EDİTÖR): Çıkarılan ham bilgileri birleştirip profesyonel bülten yazar.
    """
    
    # --- AYARLAR ---
    PARCA_BOYUTU = 10   # Güvenli limit (Hata almamak için)
    BEKLEME_SURESI = 60 # Saniye
    KARAKTER_LIMITI = 350
    
    # --- ENV KONTROL ---
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("GROQ_API_KEY")
        except:
            pass
    
    if not api_key:
        return "HATA: GROQ_API_KEY bulunamadı!"

    # --- MODEL ---
    llm = ChatGroq(
        groq_api_key=api_key,
        model_name="llama-3.3-70b-versatile",
        temperature=0.3, 
        max_retries=3
    )

    # =================================================================
    # 1. AŞAMA: MADENCİ (VERİ ÇIKARTMA)
    # =================================================================
    
    madenci_prompt = """
    Sen bir Veri Madencisisin. Görevin, verilen KAP bildirimleri arasından sadece kritik olanları ayıklamak.
    
    KURALLAR:
    1. SADECE şu konuları al: Sermaye Artırımı, Temettü, İhale/Yeni İş, Birleşme/Devralma, Geri Alım, Büyük Varlık Satışı.
    2. YAZMA: Devre kesici, Fon işlemleri, Rutin bildirimler, Borçlanma aracı, Cevaplamalar.
    3. ÇIKTI FORMATI: Sadece ham veri ver. Süsleme yapma, başlık atma.
       Örnek Satır: [ŞİRKET KODU] | [KONU TÜRÜ] | [DETAY]
    4. Eğer grupta hiç önemli haber yoksa SADECE "YOK" yaz. Başka bir şey yazma.
    """

    # Veri formatı kontrolü (String geldiyse listeye çevir)
    if isinstance(veriler_listesi, str):
        try:
            veriler_listesi = json.loads(veriler_listesi)
            if isinstance(veriler_listesi, str): # Çift katmanlıysa bir daha
                veriler_listesi = json.loads(veriler_listesi)
        except:
            return "Veri formatı hatası."

    toplam_veri = len(veriler_listesi)
    print(f"📊 Toplam {toplam_veri} bildirim taranıyor... (Madenci İş Başında)")
    
    ham_bulgular_listesi = [] # Madencinin bulduğu altınları buraya atacağız
    
    for i in range(0, toplam_veri, PARCA_BOYUTU):
        grup_ham = veriler_listesi[i : i + PARCA_BOYUTU]
        grup_no = (i // PARCA_BOYUTU) + 1
        
        # Token tasarrufu için metin hazırlığı
        grup_metin = ""
        for veri in grup_ham:
            if isinstance(veri, str): continue
            
            icerik = veri.get('icerik', '') or veri.get('summary', '') or ""
            sirket = veri.get('sirket', '')
            baslik = veri.get('baslik', '')
            
            temiz_icerik = str(icerik).replace('\n', ' ')[:KARAKTER_LIMITI]
            grup_metin += f"KOD:{sirket} | KONU:{baslik} | DETAY:{temiz_icerik}\n"

        messages = [
            ("system", madenci_prompt),
            ("human", f"TARANACAK LİSTE:\n{grup_metin}"),
        ]
        
        try:
            print(f"⛏️  Parça {grup_no} taranıyor...")
            cevap = llm.invoke(messages).content
            
            # Eğer madenci "YOK" demediyse, bulduklarını listeye ekle
            if "YOK" not in cevap:
                ham_bulgular_listesi.append(cevap)
                print(f"💎 Parça {grup_no}: Önemli bilgi bulundu!")
            else:
                print(f"System: Parça {grup_no} boş.")
                
        except Exception as e:
            print(f"⚠️ Hata (Parça {grup_no}): {e}")
        
        # Son parça değilse bekle
        if i + PARCA_BOYUTU < toplam_veri:
            print(f"⏳ Kota dolmaması için {BEKLEME_SURESI}sn bekleniyor...")
            time.sleep(BEKLEME_SURESI)

    # =================================================================
    # 2. AŞAMA: EDİTÖR (RAPORLAMA)
    # =================================================================
    
    # Eğer hiç bulgu yoksa, boş rapor dön
    if not ham_bulgular_listesi:
        return "Bugün piyasayı etkileyecek kritik bir KAP bildirimi düşmemiştir."

    print("\n📝 Editör Modu: Tüm bulgular birleştirilip raporlanıyor...")
    
    # Tüm parça parça bulguları tek bir metin haline getir
    tum_ham_metin = "\n".join(ham_bulgular_listesi)
    
    editor_prompt = """
    Sen Borsa İstanbul konusunda uzman bir Bülten Editörüsün.
    Elinde, gün içinde toplanmış dağınık haber notları var.
    
    GÖREVİN:
    Bu dağınık notları birleştirerek tek, akıcı, profesyonel bir "Gün Sonu Raporu" yazmak.
    
    KURALLAR:
    1. AYNI ŞİRKETLE İLGİLİ HABERLERİ BİRLEŞTİR: Aynı şirketin birden fazla haberi varsa alt alta yazma, tek maddede özetle.
    2. KATEGORİLERE AYIR: 
       - 💼 YENİ İŞ & İHALELER
       - 💰 SERMAYE & TEMETTÜ
       - 🤝 BİRLEŞME & SATIN ALMA
       - 🏭 YATIRIM & AR-GE
       (Hangi kategoriye uyuyorsa oraya koy)
    3. EMOJİ KULLAN: Başlıklarda ve maddelerde uygun emojiler kullan.
    4. TEKRAR ETME: Aynı bilgiyi iki kere yazma.
    5. GİRİŞ VE ÇIKIŞ METNİ YAZMA: "Merhaba işte rapor", "Saygılar" gibi şeyler yazma. Direkt raporu ver.
    6. Şirket Kodlarını (THYAO vb.) KALIN yaz.
    """
    
    messages_editor = [
        ("system", editor_prompt),
        ("human", f"İŞTE GÜNÜN DAĞINIK NOTLARI:\n{tum_ham_metin}"),
    ]
    
    try:
        final_rapor = llm.invoke(messages_editor).content
        return final_rapor
    except Exception as e:
        return f"HATA (Editör Aşaması): {e}\n\nAMA İŞTE HAM VERİLER:\n{tum_ham_metin}"

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
