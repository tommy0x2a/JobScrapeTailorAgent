To make your job-scraping & tailoring agent more **intelligent, reflective, and capable of gradual self-improvement** using the data already in SQLite (and with modest additions), you can introduce several classic agentic memory & learning patterns.

These patterns draw from 2025–2026 agent literature (Reflexion, episodic + semantic memory, self-critique loops, outcome tracking, few-shot example retrieval, preference learning, etc.) while staying realistic for a local SQLite setup.

### Most Valuable Additions (ordered roughly by impact / effort)

| # | Feature                        | Intelligence / Skill Aspect                  | DB Changes                              | Code Location & Complexity | Expected Improvement |
|---|--------------------------------|----------------------------------------------|------------------------------------------|-----------------------------|-----------------------|
| 1 | Outcome / success tracking     | Learn what actually works                    | New table + column                       | After apply / send phase    | ★★★★★ High           |
| 2 | Reflection & critique storage  | Self-critique of tailoring quality           | New table `reflections`                  | After LLM tailoring         | ★★★★☆ Very high      |
| 3 | Successful / failed examples   | Better few-shot learning in future prompts   | Reuse `jobs` + flag or new table         | Before calling LLM          | ★★★★☆ High           |
| 4 | Company / role preference memory | Remember tone, keywords, length per company/role | New table `preferences`                  | After reflection / manual feedback | ★★★☆☆ Medium-high   |
| 5 | Retrieval of similar past jobs | Contextual few-shot + pattern awareness      | Query similar jobs (keyword or simple vec) | Before LLM call             | ★★★☆☆ Medium         |
| 6 | Change / performance log       | Track how prompt / strategy evolves over time| New table `agent_runs` or `prompt_versions` | At start & end of daily run | ★★☆☆☆ Medium-low    |

### 1. Add outcome tracking (highest leverage)

Most agents improve dramatically once they can **see which applications actually got responses**.

**Schema addition**

```sql
ALTER TABLE jobs ADD COLUMN outcome TEXT DEFAULT NULL;           -- 'response', 'interview', 'rejected', 'no_reply_30d', 'ghosted', NULL
ALTER TABLE jobs ADD COLUMN outcome_date DATE DEFAULT NULL;
ALTER TABLE jobs ADD COLUMN feedback_text TEXT DEFAULT NULL;     -- optional free-text note from user
```

**Code addition** (after the daily run — can be manual or semi-automated later)

Create a simple companion script or function:

```python
def record_outcome(job_id: str, outcome: str, feedback: str = None):
    with sqlite3.connect('jobs.db') as conn:
        conn.execute("""
            UPDATE jobs 
            SET outcome = ?, outcome_date = ?, feedback_text = ?
            WHERE job_id = ?
        """, (outcome, date.today(), feedback, job_id))
        conn.commit()
```

Later you can query:

```sql
SELECT company, title, outcome, feedback_text 
FROM jobs 
WHERE outcome IS NOT NULL 
ORDER BY outcome_date DESC LIMIT 15;
```

### 2. Add reflection / self-critique step (very powerful)

After generating resume + cover letter, ask the LLM to **critique its own output**.

**New table**

```python
conn.execute('''CREATE TABLE IF NOT EXISTS reflections (
    id INTEGER PRIMARY KEY,
    job_id TEXT,
    critique TEXT,
    suggested_improvements TEXT,
    score_quality INTEGER,           -- 1–10
    score_personalization INTEGER,   -- 1–10
    created_at DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY(job_id) REFERENCES jobs(job_id)
)''')
```

**Code** — insert right after the current LLM call in the processing loop:

```python
# After getting tailored_content / data from first LLM call

reflection_prompt = f"""You just generated a tailored resume and cover letter.
Be brutally honest. Rate 1–10 and explain.

Resume:
{data['tailored_resume'][:2000]}

Cover letter:
{data['cover_letter'][:1500]}

Job description snippet:
{description[:800]}

Critique format (JSON only):
{{
  "critique": "...",
  "suggested_improvements": "...",
  "score_quality": 7,
  "score_personalization": 6
}}"""

try:
    resp = llm.invoke(reflection_prompt)
    refl = json.loads(resp.content.strip())

    cursor.execute("""
        INSERT INTO reflections 
        (job_id, critique, suggested_improvements, score_quality, score_personalization)
        VALUES (?, ?, ?, ?, ?)
    """, (job_id, refl.get("critique"), refl.get("suggested_improvements"),
          refl["score_quality"], refl["score_personalization"]))
    conn.commit()

    # Optional: if score_quality < 6, re-generate (second chance)
    if refl["score_quality"] < 6:
        log("Low quality detected → re-generating...")
        # re-call LLM with critique added to prompt
except:
    pass
```

Over time you can query lowest-scoring examples and feed them back as negative examples.

### 3. Retrieve similar past jobs → few-shot examples (strong reasoning boost)

Before calling the main tailoring LLM, retrieve 2–4 most relevant previous jobs.

**Simplest version** (keyword overlap — no embeddings needed)

```python
def get_similar_jobs(title: str, company: str, limit=3):
    like_title = f"%{title.split()[:3]}%"   # crude
    cursor.execute("""
        SELECT title, company, description, 
               tailored_resume, cover_letter   -- if you start saving them in DB too
        FROM jobs 
        WHERE processed = 1 
          AND outcome IN ('response', 'interview')   -- only good ones
          AND title LIKE ?
        ORDER BY RANDOM() LIMIT ?
    """, (like_title, limit))
    return cursor.fetchall()
```

Then inject into prompt:

```text
Successful past examples for similar roles:
{examples formatted nicely}
```

### 4. Learn company/role preferences (medium effort, good long-term value)

**Table**

```sql
CREATE TABLE IF NOT EXISTS preferences (
    id INTEGER PRIMARY KEY,
    entity_type TEXT,           -- 'company', 'role_family', 'keyword'
    entity_value TEXT,          -- 'Google', 'backend', 'AI ethics'
    preference_key TEXT,        -- 'tone', 'length', 'buzzwords_to_avoid', 'keyword_boost'
    preference_value TEXT,
    strength INTEGER DEFAULT 5, -- 1–10 how confident
    last_updated DATE
);
```

Example entries:

- company = 'Stripe' → tone = 'modern, slightly playful, mission-driven'
- role_family = 'frontend' → length = 'shorter cover letter preferred'
- keyword = 'TypeScript' → boost = 'always highlight if present in master resume'

You can populate this table manually at first, then semi-automatically from reflections or outcomes.

### Recommended Roadmap (do in this order)

1. Add `outcome` + `outcome_date` to `jobs` table (quick win)
2. Add reflection step + `reflections` table
3. Start collecting good/bad examples via outcome filter
4. Implement simple similar-job retrieval → few-shot in prompt
5. (later) Add `preferences` table + logic to update it from reflections / manual input
6. (advanced) Monthly "distillation" job: summarize patterns from high-scoring vs low-scoring tailors

Even just steps 1–3 will give your agent measurable self-improvement over 30–60 days.
