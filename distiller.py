import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict

'''
The "Distillation" script acts as the agent's long-term semantic memory generator. 
It analyzes a week's worth of granular reflections to identify high-level 
patterns—such as a specific company’s preference for brevity or a industry's obsession 
with certain keywords—and stores them as "Beliefs" to influence future runs.
* Pattern Recognition: If the agent notices three times in a row that its cover letters 
  for "Medical Device" companies are too long, this script will create a Belief like: 
  Subject: Role:Medical_Device | Belief: Keep cover letters under 200 words. 
* Prompt Injection: In the next run_agent.py cycle, you can query the beliefs table for 
  the current job's company or role type and inject that belief into the system prompt.
* Confidence Decay: Over time, you can add a script that lowers the confidence score 
  of a belief if the outcome of subsequent jobs is 'rejected', allowing the agent to 
  "unlearn" bad advice.
'''
class AgentDistiller:
    """
    Analyzes short-term reflections to create long-term semantic beliefs.
    """
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path

    def distill_weekly_patterns(self, llm):
        """
        Gathers reflections from the last 7 days and synthesizes them into beliefs.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Fetch reflections from the past week 
        one_week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT r.critique, r.suggested_improvements, j.company, j.title
            FROM reflection_log r
            JOIN jobs j ON r.job_id = j.job_id
            WHERE r.run_date >= ?
        """, (one_week_ago,))
        
        reflections = cursor.fetchall()
        if not reflections:
            print("📭 No new reflections to distill this week.")
            return

        # 2. Format reflections for the LLM
        formatted_data = "\n".join([
            f"Company: {r[2]} | Role: {r[3]}\nCritique: {r[0]}\nSuggestion: {r[1]}\n---"
            for r in reflections
        ])

        # 3. Use the LLM to find recurring patterns 
        distillation_prompt = f"""
        You are the 'Chief Strategy Officer' for an AI job agent. 
        Analyze these reflections from the past week's job applications:

        {formatted_data}

        Identify the most significant recurring pattern or 'belief' we should adopt. 
        Examples: 'San Diego startups prefer casual outreach' or 'Biotech roles require 
        heavy emphasis on documentation.'

        Return ONLY a JSON object:
        {{
          "subject": "e.g., Company:Stripe or Role:Backend",
          "belief": "The core synthesized insight",
          "evidence": "Brief summary of reflections that led to this",
          "confidence": 0.85
        }}
        """

        try:
            response = llm.invoke(distillation_prompt)
            # Standard cleanup for model response text
            cleaned_content = response.content.strip().replace('```json', '').replace('```', '')
            data = json.loads(cleaned_content)

            # 4. Save the distilled belief to the database 
            cursor.execute("""
                INSERT INTO beliefs (subject, belief, evidence, confidence, last_updated)
                VALUES (?, ?, ?, ?, ?)
            """, (data['subject'], data['belief'], data['evidence'], data['confidence'], datetime.now().date()))
            
            conn.commit()
            print(f"🧠 New Belief Formed: {data['subject']} -> {data['belief']}")

        except Exception as e:
            print(f"❌ Distillation failed: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    # This would typically be run as a weekly cron job or at the end of every 7th daily run
    from llm_router import get_llm # Assuming your LLM loader exists
    distiller = AgentDistiller()
    distiller.distill_weekly_patterns(llm=get_llm("grok"))