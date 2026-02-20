import json
import os
import time
from typing import List, Dict, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from src.logger import setup_logger

logger = setup_logger("FinancialLLM")

class FinancialLLM:
    """KAP verilerini analiz edip profesyonel bir bülten oluşturan Yapay Zeka sınıfı."""
    
    def __init__(self, model_name: str = "llama-3.3-70b-versatile", temp: float = 0.3):
        # API Anahtarını al
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.error("GROQ_API_KEY bulunamadı! Lütfen .env dosyasını kontrol edin.")
            raise ValueError("Groq API Key eksik.")
            
        # Parametreleri ve LLM'i başlat
        self.chunk_size = 10
        self.sleep_time = 65
        self.char_limit = 350
        
        self.llm = ChatGroq(
            groq_api_key=self.api_key,
            model_name=model_name,
            temperature=temp,
            max_retries=3
        )
        logger.info(f"FinancialLLM başlatıldı. (Model: {model_name})")

    def _mine_data(self, veriler: List[Dict]) -> List[str]:
        """AŞAMA 1: Verileri parçalar halinde tarar ve ham bulguları çıkarır."""
        madenci_prompt = """
        Sen bir Veri Madencisisin. Görevin, verilen KAP bildirimleri arasından sadece kritik olanları ayıklamak.
        KURALLAR:
        1. SADECE şu konuları al: Sermaye Artırımı, Temettü, İhale/Yeni İş, Birleşme/Devralma, Geri Alım, Büyük Varlık Satışı.
        2. YAZMA: Devre kesici, Fon işlemleri, Rutin bildirimler, Borçlanma aracı ihracı vb.
        3. ÇIKTI FORMATI: Sadece ham veri ver. Süsleme yapma. (Örn: THYAO | YENİ İŞ | 50M$ sözleşme imzaladı)
        4. Eğer grupta hiç önemli haber yoksa SADECE "YOK" yaz.
        """
        
        toplam_veri = len(veriler)
        logger.info(f"Toplam {toplam_veri} bildirim taranıyor... (Madenci Modu)")
        ham_bulgular = []
        
        for i in range(0, toplam_veri, self.chunk_size):
            grup = veriler[i : i + self.chunk_size]
            grup_no = (i // self.chunk_size) + 1
            
            grup_metin = ""
            for v in grup:
                icerik = str(v.get('icerik', '')).replace('\n', ' ')[:self.char_limit]
                grup_metin += f"KOD:{v.get('sirket')} | KONU:{v.get('baslik')} | DETAY:{icerik}\n"

            messages = [
                ("system", madenci_prompt),
                ("human", f"LİSTE:\n{grup_metin}"),
            ]
            
            try:
                cevap = self.llm.invoke(messages).content
                if "YOK" not in cevap and len(cevap) > 5:
                    ham_bulgular.append(cevap)
                    logger.info(f"Parça {grup_no}: Önemli bilgi bulundu.")
                else:
                    logger.debug(f"Parça {grup_no}: Boş geçildi.")
            except Exception as e:
                logger.error(f"Parça {grup_no} analizi başarısız: {e}")
                
            # Rate limit koruması
            if i + self.chunk_size < toplam_veri:
                logger.info(f"Kota koruması: {self.sleep_time} saniye bekleniyor...")
                time.sleep(self.sleep_time)
                
        return ham_bulgular

    def _edit_report(self, ham_bulgular: List[str]) -> str:
        """AŞAMA 2: Madencinin bulduğu verileri birleştirip bülten yazar."""
        tum_metin = "\n".join(ham_bulgular)
        
        editor_prompt = """
        Sen Borsa İstanbul konusunda uzman bir Bülten Editörüsün.
        GÖREVİN: Dağınık notları birleştirerek tek, akıcı, profesyonel bir "Gün Sonu Raporu" yazmak.
        KURALLAR:
        1. Aynı şirketle ilgili haberleri tek maddede birleştir.
        2. Kategorilere ayır (💼 YENİ İŞ & İHALELER, 💰 SERMAYE & TEMETTÜ vb.)
        3. Giriş veya çıkış/selamlama metni yazma. Sadece raporu ver.
        4. Şirket Kodlarını KALIN yaz.
        """
        
        messages = [
            ("system", editor_prompt),
            ("human", f"GÜNÜN NOTLARI:\n{tum_metin}"),
        ]
        
        logger.info("Editör Modu: Rapor derleniyor...")
        try:
            return self.llm.invoke(messages).content
        except Exception as e:
            logger.error(f"Editör aşamasında hata: {e}")
            return "Rapor derlenirken bir hata oluştu."

    def analyze(self, veriler: List[Dict]) -> str:
        """Ana fonksiyon: Madenci ve Editör süreçlerini yönetir."""
        if not veriler:
            logger.warning("Analiz edilecek veri yok!")
            return "Bugün KAP'a düşen bildirim bulunmamaktadır."
            
        # 1. Aşama
        bulgular = self._mine_data(veriler)
        
        if not bulgular:
            return "Bugün piyasayı etkileyecek kritik bir KAP bildirimi düşmemiştir."
            
        # 2. Aşama
        final_rapor = self._edit_report(bulgular)
        logger.info("Yapay zeka analizi başarıyla tamamlandı.")
        return final_rapor