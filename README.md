# 📈 KAP AI Analyst: Enterprise-Grade Financial Intelligence Bot

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![LangChain](https://img.shields.io/badge/LangChain-AI-orange?style=for-the-badge)
![Groq](https://img.shields.io/badge/LLM-Llama_3.3_70B-black?style=for-the-badge&logo=meta)
![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions)
![Telegram](https://img.shields.io/badge/Delivery-Telegram_API-2CA5E0?style=for-the-badge&logo=telegram)
![Architecture](https://img.shields.io/badge/Architecture-OOP_%7C_Map--Reduce-success?style=for-the-badge)

> **Automated, AI-driven financial insights delivered directly to your pocket.**

KAP AI Analyst is a production-ready, serverless automation tool designed to scrape, analyze, and summarize daily disclosures from Borsa Istanbul (KAP). Built with **Object-Oriented Programming (OOP)** principles and a **Map-Reduce LLM architecture**, it filters out market noise and delivers high-value, categorized financial summaries via Telegram.

---

## 🌟 Key Features

* **🧠 Advanced AI Engine (Map-Reduce):** Solves LLM token limits and context loss by using a two-stage analysis pipeline. Stage 1 (Miner) extracts raw data in chunks. Stage 2 (Editor) synthesizes it into a cohesive, categorized bulletin.
* **🏗️ Enterprise Architecture:** Fully modular design (`Scraper`, `Analyzer`, `Notifier`, `Orchestrator`) adhering to SOLID principles.
* **🛡️ Robust Error Handling & Logging:** Integrated Python `logging` with file and console handlers, ensuring traceability and easy debugging.
* **⚙️ 100% Serverless & Zero-Cost:** Fully automated via **GitHub Actions** Cron Jobs. No servers to maintain.
* **📦 Smart Scraping:** Handles complex nested HTML and dynamic JSON payloads to extract data that standard APIs miss.

---

## 🏗️ System Architecture

The project is structured into independent modules orchestrated by a central pipeline.

```mermaid
graph TD
    A[KAP Web API] -->|Scraping & Cleaning| B(src/scraper.py)
    B -->|Raw Disclosures| C{src/analyzer.py}
    
    subgraph AI Pipeline: Map-Reduce
    C -->|Chunking 10 items/batch| D[Miner LLM]
    D -->|Extracts Core Events| E[Raw Insights List]
    E -->|Combine| F[Editor LLM]
    F -->|Categorize & Format| G[Final Bulletin]
    end
    
    G -->|Markdown Text| H(src/notifier.py)
    H -->|API Request| I[Telegram Channel]
    
    subgraph GitHub Actions: CI/CD
    J((Cron Job 18:30)) -->|Triggers| K[src/main.py Orchestrator]
    K --> B
    end
