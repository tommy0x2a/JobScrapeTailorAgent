from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

# This ensures your database always receives the same "contract" of data.
class JobLead(BaseModel):
    job_id: str
    title: str
    company: str
    location: str = "San Diego, CA"
    url: str
    description: str
    posted_date: str = str(date.today())
    source_method: str  # e.g., "Crawl4AI", "Gmail", "BS4"
    raw_json: Optional[str] = None