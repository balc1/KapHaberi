import json
import os
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from dotenv import load_dotenv

# .env dosyasını yükler (API KEY buradan gelir)
load_dotenv()

# --- LLM FONKSİYONU ---
# Bu fonksiyon artık dışarıdan 'json_input_str' adında veri bekliyor
def llm_response(json_input_str):
    
    # SYSTEM PROMPT (Senin yazdığın harika prompt)
    system_prompt = """
    Sen Borsa İstanbul konusunda uzman, kıdemli bir Finansal Analistsin. 
    Görevin: Sana JSON formatında verilen KAP bildirimlerini analiz etmek ve yatırımcı için bir 'Gün Sonu Raporu' hazırlamak.

    Aşağıdaki KURALLARA sıkı sıkıya uy:

    1. **FİLTRELEME (ÖNEMLİ vs ÖNEMSİZ):**
       - **ÖNEMLİ:** Sermaye Artırımı, Temettü, Yeni İş İlişkisi (İhale/Sipariş), Birleşme/Devralma, Geri Alım (Buyback), Büyük Duran Varlık Satışı, Finansal Duran Varlık Edinimi.
       - **ÖNEMSİZ (YAZMA):** Devre Kesici, Volatilite Bazlı Tedbir, Fon İşlemleri, Rutin Genel Kurul Kayıtları, SGK/Vergi Borcu Yoktur yazıları, Sermaye Piyasası Aracı İhracı (Tahvil/Bono satışı - hisse senedi değilse), Personel atamaları (CEO değilse).

    2. **ÖZETLEME FORMATI:**
       - Sadece "ÖNEMLİ" kategorisine girenleri raporla.
       - Her şirket için madde işareti kullan.
       - Şirket Kodu ve Adını Kalın Yaz.
       - Bildirimi 1-2 cümle ile, yatırımcı gözüyle özetle. (Örn: "Şirket, 50 Milyon TL değerinde yeni bir güneş enerjisi ihalesi kazandı. Ciroya etkisi %5 olacak.")
       - Asla JSON formatında cevap verme, okunabilir bir Rapor metni yaz.

    3. **TON:**
       - Profesyonel, net ve kısa.

    Eğer hiç önemli haber yoksa "Bugün piyasayı etkileyecek kritik bir KAP bildirimi düşmemiştir." yaz.
    """

    llm = ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile",
        temperature=0.3,
        top_p=0.9,
        max_tokens=10000
    )

    # MESAJLARI OLUŞTURUYORUZ
    # System: Kuralları veriyoruz
    # Human: Okuduğumuz JSON verisini veriyoruz
    messages = [
        ("system", system_prompt),
        ("human", f"İşte bugünün KAP verileri, bunları analiz et: {json_input_str}"),
    ]
    
    # Modele gönder ve cevabı al
    response = llm.invoke(messages)
    return response.content

# --- ANA ÇALIŞMA ALANI ---
if __name__ == "__main__":
    
    # 1. JSON DOSYASINI OKU
    # Not: Dosya adı her gün değişeceği için burayı dinamik yapabiliriz ileride.
    dosya_adi = "kap_verileri_28_01_2026.json" 
    
    try:
        print(f"'{dosya_adi}' okunuyor...")
        with open(dosya_adi, "r", encoding="utf-8") as f:
            ham_veri = json.load(f)
        
        # 2. VERİYİ STRING FORMATINA ÇEVİR (LLM JSON objesi okumaz, yazı okur)
        # ensure_ascii=False çok önemli, yoksa Türkçe karakterler bozuk gider.
        user_message_str = json.dumps(ham_veri, ensure_ascii=False)

        print("Groq Analiz Ediyor... (Lütfen bekleyin)")

        # 3. FONKSİYONA VERİYİ GÖNDER
        analiz_sonucu = llm_response(user_message_str)

        # 4. SONUCU YAZDIR
        print("\n" + "="*40)
        print("GÜN SONU FİNANSAL RAPORU")
        print("="*40)
        print(analiz_sonucu)

        # 5. RAPORU KAYDET
        with open("GUN_SONU_RAPORU.txt", "w", encoding="utf-8") as f:
            f.write(analiz_sonucu)
            print("\nRapor 'GUN_SONU_RAPORU.txt' dosyasına kaydedildi.")

    except FileNotFoundError:
        print(f"HATA: '{dosya_adi}' bulunamadı. Lütfen önce veri çekme kodunu çalıştırın.")
    except Exception as e:
        print(f"Beklenmeyen bir hata oluştu: {e}")