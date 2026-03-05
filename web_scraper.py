from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from models import JobLead
import hashlib

class WebScraper:
    """
    Handles JS-heavy job boards using Crawl4AI to generate LLM-ready Markdown.
    """
    async def scrape(self, url: str, entity_name: str) -> list[JobLead]:
        browser_config = BrowserConfig(headless=True, java_script_enabled=True)
        run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)
            if not result.success:
                return []

            # [cite_start]Generate a deterministic ID [cite: 6]
            job_id = hashlib.sha256(f"{url}{entity_name}".encode()).hexdigest()[:32]
            
            return [JobLead(
                job_id=job_id,
                title="Pending Extraction", # LLM Node will refine this later
                company=entity_name,
                url=url,
                description=result.markdown, # Clean markdown for the LLM
                source_method="Crawl4AI"
            )]