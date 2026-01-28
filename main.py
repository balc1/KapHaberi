import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

# --- MODÜLLERİ İÇE AKTAR ---
# Eğer dosya adların farklıysa buradaki isimleri değiştirmen gerekir.
try:
    from veri_cekme import gun_sonu_verisi_topla
    from analiz import llm_response
    from mail_servisi import mail_gonder
except ImportError as e:
    print(f"KRİTİK HATA: Modüller bulunamadı! Dosya adlarını kontrol et.\nHata: {e}")
    sys.exit(1)

# .env dosyasını yükle
load_dotenv()

def akis_baslat():
    """
    Bu fonksiyon sırasıyla:
    1. KAP verisini çeker.
    2. LLM'e analiz ettirir.
    3. Sonucu e-posta atar.
    """
    baslangic_zamani = datetime.now()
    bugun_str = baslangic_zamani.strftime("%d.%m.%Y")
    
    print(f"\n🚀 BORSA BOTU ÇALIŞTIRILIYOR - {bugun_str}")
    print("="*50)

    # --- ADIM 1: VERİ TOPLAMA ---
    print("\n[ADIM 1/3] KAP Verileri Çekiliyor...")
    try:
        veriler = gun_sonu_verisi_topla()
        
        if not veriler:
            print("⚠️ UYARI: Bugün hiç bildirim yok veya veri çekilemedi. İşlem sonlandırılıyor.")
            return # E-posta atmadan çık
            
        print(f"✅ Başarılı: {len(veriler)} adet ham veri toplandı.")
        
    except Exception as e:
        print(f"❌ HATA (Veri Çekme): {e}")
        # İstersen buraya hata bildirim maili ekleyebilirsin
        return

    # --- ADIM 2: ANALİZ (GROQ) ---
    print("\n[ADIM 2/3] Yapay Zeka Analizi Başlıyor...")
    try:
        # LLM'e göndermek için JSON stringine çevir
        json_input = json.dumps(veriler, ensure_ascii=False)
        
        rapor_metni = llm_response(json_input)
        
        if not rapor_metni:
            print("❌ HATA: LLM boş cevap döndü.")
            return

        print("✅ Analiz tamamlandı.")
        
        # (Opsiyonel) Raporu bilgisayara da yedekle
        yedek_dosya = f"rapor_{baslangic_zamani.strftime('%Y%m%d')}.txt"
        with open(yedek_dosya, "w", encoding="utf-8") as f:
            f.write(rapor_metni)

    except Exception as e:
        print(f"❌ HATA (Analiz): {e}")
        return

    # --- ADIM 3: E-POSTA GÖNDERİMİ ---
    print("\n[ADIM 3/3] Rapor Gönderiliyor...")
    try:
        konu_basligi = f"📅 Borsa Gün Sonu Raporu | {bugun_str}"
        
        basari = mail_gonder(konu_basligi, rapor_metni)
        
        if basari:
            print(f"✅ E-posta başarıyla gönderildi: {konu_basligi}")
        else:
            print("❌ E-posta gönderilemedi (Mail servisi hatası).")

    except Exception as e:
        print(f"❌ HATA (Mail): {e}")

    # --- BİTİŞ ---
    gecen_sure = datetime.now() - baslangic_zamani
    print("="*50)
    print(f"🏁 İŞLEM TAMAMLANDI. (Süre: {gecen_sure})")

if __name__ == "__main__":
    akis_baslat()