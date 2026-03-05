import asyncio
from web_scraper import WebScraper
from email_scraper import EmailScraper
from models import JobLead

async def main():
    # 1. Initialization
    web = WebScraper()
    email = EmailScraper()
    all_discovered_leads = []

    # 2. Configurable Search Data Structure
    # This can easily be moved to a separate config.py or .json file
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
        # Email-based "boards" or specific email queries
        {"name": "myemailaddress.com", "query": "label:INBOX 'software engineer' San Diego", "type": "email"},
        {"name": "Niche_Newsletter", "query": "from:newsletter@example.com 'hiring'", "type": "email"}
    ]

    print(f"🚀 Starting Daily Run: Iterating through {len(JOB_SOURCES)} sources...")

    # 3. Polymorphic Iteration Loop
    for source in JOB_SOURCES:
        try:
            print(f"🔍 Checking {source['name']}...")
            
            if source["type"] == "web":
                # Crawl4AI handles the rendering and markdown conversion
                leads = await web.scrape(source["url"], source["name"])
                all_discovered_leads.extend(leads)
                
            elif source["type"] == "email":
                # Gmail API handles the inbox search and decoding
                leads = await email.scrape_inbox(source["query"])
                all_discovered_leads.extend(leads)
                
            # Respectful rate limiting to avoid getting flagged 
            await asyncio.sleep(2) 

        except Exception as e:
            print(f"⚠️ Error scraping {source['name']}: {e}")

    # 4. Final Processing
    print(f"✅ Run Complete. Total Leads Found: {len(all_discovered_leads)}")
    # Next: Pass all_discovered_leads to your DB and LLM nodes

if __name__ == "__main__":
    asyncio.run(main())