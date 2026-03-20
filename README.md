# JobScrapeTailorAgent 🚀

**JobScrapeTailorAgent** is a modular, autonomous job-hunting system specialized for software engineering roles in San Diego, CA. It automates the entire funnel: from deep-web scraping and Gmail inbox monitoring to AI-powered resume tailoring and contact management.

---

## 🛠️ System Architecture

The agent is designed with a "Single Responsibility" architecture, separating web scraping, email extraction, and AI reasoning into distinct, scalable modules.

### Core Components

* 
**`run_agent.py`**: The central orchestrator that iterates through sources and manages the execution flow.


* **`web_scraper.py`**: Utilizes **Crawl4AI** to handle JavaScript-heavy sites (LinkedIn, Indeed) and convert them into LLM-ready Markdown.
* 
**`email_scraper.py`**: Uses the **Gmail API** to pull job leads directly from your inbox or newsletters.


* **`scraper_router.py`**: A polymorphic router that directs each job board to the most efficient scraping method.
* **`models.py`**: Contains the **Pydantic `JobLead**` model to ensure data consistency across all sources.
* 
**`database.py`**: Manages the SQLite `jobs.db`, including self-improving memory tables like `reflection_log` and `tailoring_patterns`.



---

## 📋 Features

* **Polymorphic Scraping**: Supports Crawl4AI, BeautifulSoup, and direct Gmail API extraction in a single loop.
* 
**Self-Improving Memory**: Tracks "lessons learned" from past tailoring runs to improve keyword matching over time.


* 
**San Diego Focus**: Hardcoded logic to prioritize and sanitize leads within the San Diego metro area.


* 
**Automated Artifacts**: Generates specialized `resume.md`, `cover_letter.md`, and `email_interest.md` files for every new lead.



---

## 🚀 Getting Started

### 1. Prerequisites

* Python 3.10+
* Google Cloud Project with **Gmail API** enabled.
* [Crawl4AI](https://github.com/unclecode/crawl4ai) and Playwright.

### 2. Installation

```bash
pip install -r requirements.txt
playwright install chromium

```

### 3. Configuration

1. **Gmail**: Place your `credentials.json` in the root folder. On the first run, the agent will prompt for OAuth approval and save a `token.json`.


2. 
**Resume**: Place your master `resume.md` in the root directory.


3. **Environment**: Create a `.env` file with your API keys:
```env
# =================================================================
# 🔑 LLM & AI ORCHESTRATION
# =================================================================
# Primary model for tailoring resumes and generating cover letters.
# If XAI is present, the agent defaults to 'grok-beta'. [cite: 1, 10]
XAI_API_KEY="your_xai_api_key_here"

# Backup or primary alternative for LangGraph orchestration.
GEMINI_API_KEY="your_gemini_api_key_here"

# standard fallback for OpenAI-compatible client libraries. [cite: 1, 10]
OPENAI_API_KEY="your_openai_api_key_here"

# =================================================================
# 🔍 SEARCH & SCRAPING TOOLS
# =================================================================
# Used by ScraperRouter for high-speed Google Jobs API results.
# Get a free key at serper.dev (supports "San Diego" geo-location). 
SERPER_API_KEY="your_serper_api_key_here"

# Alternative to Serper if using the original Google Search logic. [cite: 1]
SERPAPI_API_KEY="your_serpapi_key_here"

# =================================================================
# ⚙️ AGENT CONFIGURATION
# =================================================================
# Set to 'true' to run LLMs locally via Ollama/LlamaEdge. 
USE_LOCAL=true

# The email address to target for 'myemailaddress.com' logic. [cite: 5, 9]
TARGET_EMAIL="myEmail@service.com"

# =================================================================
# 📁 DIRECTORY & DB PATHS
# =================================================================
# Path to the SQLite memory and jobs storage. [cite: 2, 6, 9]
DATABASE_PATH="jobs.db"

# Path to your master markdown resume. [cite: 1, 7, 9]
MASTER_RESUME_PATH="resume.md"

# Folder where tailored job artifacts are saved. [cite: 1, 8, 9]
OUTPUT_DIR="jobs/"

```



### 4. Running the Agent

```python
python run_agent.py

```

---

## 📊 Database Schema

The system maintains a local `jobs.db` with the following memory-enhanced tables:

* **`jobs`**: Main repository for all discovered leads.
* **`reflection_log`**: Stores self-critiques and procedural improvements.
* **`tailoring_patterns`**: Tracks which resume bullet changes resulted in the highest quality matches.
* **`beliefs`**: Maintains confidence scores for specific recruiters and companies.

---

## ⚖️ Rules & Safeguards

* 
**Human-in-the-Loop**: The agent prepares applications but **never** sends emails automatically.


* 
**Ethical Scraping**: Implements rate limiting and respects `robots.txt` where applicable.


* 
**Data Security**: Keeps all job and personal data within a local SQLite database.



---

