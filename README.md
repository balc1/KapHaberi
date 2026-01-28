# 📈 KAP AI Analyst: Borsa İstanbul Akıllı Asistanı

![Python](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python)
![Groq](https://img.shields.io/badge/AI-Llama3.3-orange?style=for-the-badge)
![GitHub Actions](https://img.shields.io/badge/Automation-GitHub%20Actions-2088FF?style=for-the-badge&logo=github-actions)
![Telegram](https://img.shields.io/badge/Notification-Telegram-2CA5E0?style=for-the-badge&logo=telegram)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

> **"Bilgi güçtür, ancak filtrelenmiş bilgi kazançtır."**

Bu proje, Borsa İstanbul'daki şirketlerin **KAP (Kamuyu Aydınlatma Platformu)** üzerinde yayınladığı yüzlerce bildirimi her gün otomatik olarak tarar, **Yapay Zeka (LLM)** ile analiz eder, önemsizleri eler ve kritik gelişmeleri özetleyerek **Telegram Kanalına** raporlar.

---

## 🚀 Projenin Amacı

Borsa yatırımcıları için her gün yüzlerce KAP bildirimi düşer. Bunların %90'ı "Devre Kesici", "Fon İşlemleri" gibi rutin ve fiyata etkisi olmayan bildirimlerdir.
Bu botun amacı:
1.  Yatırımcının zaman kaybını önlemek.
2.  **Sermaye Artırımı, Yeni İş İlişkisi, İhale** gibi kritik haberleri gürültüden ayıklamak.
3.  Karmaşık finansal dili, herkesin anlayabileceği net bir özete dönüştürmek.

## 🏗️ Mimari ve Çalışma Mantığı

Bu proje **Serverless (Sunucusuz)** mimari ile tasarlanmıştır ve **0 maliyetle** çalışır.

```mermaid
graph LR
A[KAP Web Sitesi] -->|Scraping| B(Veri Toplama Modülü)
B -->|JSON Veri| C{Yapay Zeka Analizi}
C -->|Llama-3.3 on Groq| D[Finansal Filtreleme]
D -->|Özet Rapor| E[Telegram Kanalı]
subgraph GitHub Actions [Otomasyon - Her Gün 18:30]
B
C
D
E
end
