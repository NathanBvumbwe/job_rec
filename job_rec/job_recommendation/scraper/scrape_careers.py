import psycopg2
from datetime import datetime, timedelta
import logging
import asyncio
import re
import os
import django
from django.conf import settings
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
# ... other selenium imports ...
from bs4 import BeautifulSoup
from asgiref.sync import sync_to_async

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_rec.settings')
django.setup()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@sync_to_async
def save_job(job):
    from job_recommendation.models import Job
    obj, created = Job.objects.get_or_create(
        url=job.get("url"),
        defaults={
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "job_type": job.get("job_type"),
            "date_posted": job.get("date_posted"),
            "source": job.get("source"),
            "description": job.get("description"),
        }
    )
    return created

async def scrape_careersmw(): # Or scrape_ntchito, etc.
    print("Current working directory:", os.getcwd())
    base_url = "https://careersmw.com/jobs/" # Change this for each scraper
    jobs = []
    
    driver = None
    try:
        # ... (Selenium setup and your specific scraping logic to fill the 'jobs' list) ...
        if driver:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            job_elements = soup.select("article.job-card") or soup.select("div.job-listing") or soup.find_all("li", class_="job")
            logger.info(f"Found {len(job_elements)} potential job elements on the page")
            if not job_elements:
                logger.error("No job elements found! Check selector or page structure.")
            for job_elem in job_elements:
                try:
                    url_elem = (job_elem.find("a", class_="job-card-title") or
                                job_elem.find("a", class_="title") or
                                job_elem.find("a", href=True))
                    job_url = url_elem['href'] if url_elem and url_elem.has_attr('href') else None
                    title = url_elem.text.strip() if url_elem else 'N/A'
                    company_elem = (job_elem.select_one("span.job-card-company") or
                                    job_elem.select_one("span.company") or
                                    job_elem.find("span", class_="company"))
                    company = company_elem.text.strip() if company_elem else 'N/A'
                    location_elem = (job_elem.select_one("li.job-card-location") or
                                     job_elem.select_one("span.location") or
                                     job_elem.find("span", class_="location"))
                    location = location_elem.text.strip() if location_elem else 'N/A'
                    job_type_elem = (job_elem.select_one("li.job-card-type") or
                                     job_elem.select_one("span.job-type") or
                                     job_elem.find("span", class_="job-type"))
                    job_type = job_type_elem.text.strip() if job_type_elem else 'N/A'
                    date_posted = datetime.now().date()
                    job_data = {
                        "title": title,
                        "company": company,
                        "location": location,
                        "job_type": job_type,
                        "date_posted": date_posted,
                        "url": job_url,
                        "source": "careersmw.com",
                        "description": "N/A",
                    }
                    if not job_url:
                        logger.warning(f"Missing job URL for job: {title}")
                    jobs.append(job_data)
                    logger.info(f"Parsed job: {job_data['title']}")
                except Exception as e:
                    logger.warning(f"Could not parse a job element: {e}")
        # --- Save to database ---
        if jobs:
            inserted = 0
            for job in jobs:
                try:
                    created = await save_job(job)
                    if created:
                        inserted += 1
                except Exception as e:
                    logger.warning(f"Failed to insert job {job.get('url')}: {e}")
            logger.info(f"Saved {inserted} jobs from careersmw.com to database")
        else:
            logger.warning("No jobs were scraped from careersmw.com to save.")
    finally:
        if driver:
            driver.save_screenshot("careersmw_final.png")
            with open("careersmw_final_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            driver.quit()