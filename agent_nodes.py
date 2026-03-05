import os
import json
import hashlib
from datetime import date
from pydantic import BaseModel, Field
from typing import List, Optional

# Structured Output Schema for the LLM
class TailoredOutput(BaseModel):
    resume: str = Field(description="The tailored markdown resume")
    cover_letter: str = Field(description="A 3-paragraph personalized cover letter")
    email_subject: str
    email_body: str
    reflection: str = Field(description="A lesson learned for future tailoring")

class JobAgentNodes:
    def __init__(self, llm, db_conn):
        self.llm = llm # Bind your Gemini or Grok model here
        self.db = db_conn

    def scrape_and_score(self, search_results: List[dict]):
        """Scores jobs (0-100) based on personal relevance before processing."""
        cursor = self.db.cursor()
        for job in search_results:
            job_id = hashlib.sha256(f"{job['title']}{job['company']}".encode()).hexdigest()[:32]
            
            # Simple Scoring Logic (can be upgraded to LLM-based scoring)
            score = 100 if "Python" in job['description'] else 50
            
            cursor.execute("""
                INSERT OR IGNORE INTO jobs (job_id, title, company, description, url, score, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (job_id, job['title'], job['company'], job['description'], job['url'], score, date.today()))
        self.db.commit()

    def retrieve_memories(self, job_description: str):
        """Fetches top 3 relevant lessons from past runs."""
        cursor = self.db.cursor()
        cursor.execute("SELECT lesson FROM reflection_log ORDER BY id DESC LIMIT 3")
        return [row[0] for row in cursor.fetchall()]

    def tailor_job(self, job_data: dict, master_resume: str):
        """The core tailoring node using memories and master resume[cite: 7, 9]."""
        memories = self.retrieve_memories(job_data['description'])
        
        prompt = f"""
        MASTER RESUME: {master_resume}
        JOB DESCRIPTION: {job_data['description']}
        PAST LESSONS: {memories}
        
        Tailor this resume. Rewrite bullets to match keywords. 
        Focus on San Diego localization. [cite: 4, 8]
        """
        
        # Using structured output (requires LangChain/Gemini tool binding)
        structured_llm = self.llm.with_structured_output(TailoredOutput)
        output = structured_llm.invoke(prompt)
        
        # Save files and record the reflection
        self._save_artifacts(job_data, output)
        self._record_reflection(output.reflection)

    def _save_artifacts(self, job, output):
        path = f"jobs/{job['company']}/{job['title']}".replace(" ", "_")
        os.makedirs(path, exist_ok=True)
        with open(f"{path}/resume.md", "w") as f: f.write(output.resume)
        with open(f"{path}/cover_letter.md", "w") as f: f.write(output.cover_letter)
        # Add contact info and email [cite: 8]