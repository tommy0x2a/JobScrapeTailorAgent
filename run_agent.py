import sqlite3
import json
import os
from datetime import date, datetime
import asyncio
from web_scraper import WebScraper
from email_scraper import EmailScraper
from models import JobLead
from database import init_db
from distiller import AgentDistiller  # Ensure this matches your filename
from dotenv import load_dotenv

load_dotenv()

# Helper for file saving
def save_job_artifacts(company, title, data):
    # Sanitize folder names 
    folder = f"jobs/{company.replace(' ', '_')}/{title.replace(' ', '_')}"[:100]
    os.makedirs(folder, exist_ok=True)
    with open(f"{folder}/resume.md", "w", encoding="utf-8") as f: 
        f.write(data.get('tailored_resume', ''))
    with open(f"{folder}/cover_letter.md", "w", encoding="utf-8") as f: 
        f.write(data.get('cover_letter', ''))
    with open(f"{folder}/email_outreach.md", "w", encoding="utf-8") as f:
        f.write(f"Subject: {data.get('email_subject', '')}\n\n{data.get('email_body', '')}")

async def main():
    # 1. Initialization
    db_conn = init_db()
    web = WebScraper()
    email = EmailScraper()
    
    # Initialize your chosen LLM (Example using LangChain style)
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))

    # 2. Configurable Search Data Structure
    JOB_SOURCES = [
        {"name": "LinkedIn", "url": "https://www.linkedin.com/jobs/search?keywords=python&location=San%20Diego", "type": "web"},
        {"name": "Indeed", "url": "https://www.indeed.com/jobs?q=python+software+engineer&l=San+Diego%2C+CA", "type": "web"},
        {"name": "Glassdoor", "url": "https://www.glassdoor.com/Job/san-diego-python-developer-jobs-SRCH_IL.0,9_IC1147311_KO10,26.htm", "type": "web"},
        {"name": "Dice", "url": "https://www.dice.com/jobs?q=python&l=San%20Diego,%20CA", "type": "web"},
        {"name": "ZipRecruiter", "url": "https://www.ziprecruiter.com/Jobs/Python/-in-San-Diego,CA", "type": "web"},
        {"name": "BuiltIn", "url": "https://www.builtin.com/jobs/dev-engineering/python/san-diego", "type": "web"},
        {"name": "Wellfound", "url": "https://wellfound.com/role/l/python-developer/san-diego", "type": "web"},
        {"name": "Craigslist", "url": "https://sandiego.craigslist.org/search/jjj?query=python", "type": "web"},
        {"name": "USAJobs", "url": "https://www.usajobs.gov/Search/Results?l=San%20Diego%2C%20California&k=software%20engineer", "type": "web"},
        {"name": "X_Jobs", "url": "https://x.com/jobs", "type": "web"},
        # Email-based boards explicitly including myemailaddress.com
        {"name": "myemailaddress.com", "query": "label:INBOX 'software engineer' San Diego", "type": "email"},
        {"name": "Niche_Newsletter", "query": "from:newsletter@example.com 'hiring'", "type": "email"}
    ]

    print(f"🚀 PHASE 1: Discovery - Iterating through {len(JOB_SOURCES)} sources...")

    # 3. Polymorphic Iteration & DB Storage
    for source in JOB_SOURCES:
        try:
            print(f"🔍 Checking {source['name']}...")
            leads = []
            if source["type"] == "web":
                leads = await web.scrape(source["url"], source["name"])
            elif source["type"] == "email":
                leads = await email.scrape_inbox(source["query"])
            
            # UPSERT into database 
            cursor = db_conn.cursor()
            for lead in leads:
                cursor.execute("""
                    INSERT OR IGNORE INTO jobs (job_id, title, company, url, description, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (lead.job_id, lead.title, lead.company, lead.url, lead.description, date.today()))
            db_conn.commit()
            await asyncio.sleep(2) 

        except Exception as e:
            print(f"⚠️ Error scraping {source['name']}: {e}")
    
    # 4. Processing Phase (AI Tailoring)
    print("\n🤖 PHASE 2: AI Processing & Tailoring...")
    await processing_phase(llm, db_conn)

    # 5. Weekly Distillation (Self-Improvement)
    # Triggered if it's Sunday or if specifically called
    if datetime.now().weekday() == 6:
        print("\n🧠 PHASE 3: Weekly Distillation (Synthesizing Beliefs)...")
        distiller = AgentDistiller()
        distiller.distill_weekly_patterns(llm)

    db_conn.close()
    print("\n✅ DAILY RUN COMPLETE.")

async def processing_phase(llm, db_conn):
    cursor = db_conn.cursor()
    
    # 1. Fetch unprocessed jobs 
    cursor.execute("SELECT * FROM jobs WHERE processed = 0 ORDER BY score DESC LIMIT 5")
    rows = cursor.fetchall()

    for row in rows:
        (job_id, title, company, location, posted_date, url, description, 
         score, processed, last_seen) = row

        print(f"🛠️  Tailoring: {title} @ {company}")

        # 🧠 INTELLIGENCE STEP: Fetch relevant beliefs 
        cursor.execute("""
            SELECT belief FROM beliefs 
            WHERE (subject LIKE ? OR subject LIKE ?) AND confidence > 0.6
            ORDER BY confidence DESC LIMIT 3
        """, (f"%{company}%", f"%{title.split()[0]}%"))
        
        beliefs = cursor.fetchall()
        beliefs_context = "\n".join([f"- {b[0]}" for b in beliefs])

        # 2. Load Master Resume [cite: 7, 8]
        with open("resume.md", "r", encoding="utf-8") as f:
            master_resume = f.read()

        # 3. Structured JSON Prompt 
        prompt = f"""You are an expert resume writer and career coach.
Tailor the resume, write a strong cover letter, and a short personalized outreach email for this exact job.

MASTER RESUME:
{master_resume}

JOB DESCRIPTION:
{description[:1500]}

STRATEGIC BELIEFS & PATTERNS:
{beliefs_context if beliefs_context else "Use standard high-quality tailoring."}

Return ONLY a valid JSON object:
{{
  "tailored_resume": "markdown_content",
  "cover_letter": "markdown_content",
  "email_subject": "subject_line",
  "email_body": "personalized_body"
}}"""

        try:
            # 4. AI INVOKE LLM with prompt and injected beliefs
            response = llm.invoke(prompt)
            data = json.loads(response.content.strip().replace('```json', '').replace('```', ''))

            # 5. Save Artifacts 
            save_job_artifacts(company, title, data)
            
            # 6. Mark as processed 
            cursor.execute("UPDATE jobs SET processed = 1, last_seen = ? WHERE job_id = ?", 
                           (date.today(), job_id))
            db_conn.commit()

        except Exception as e:
            print(f"❌ Error processing {title}: {e}")

if __name__ == "__main__":
    asyncio.run(main())