import psycopg2
from datetime import datetime
import logging
import asyncio
import re
import os
import django
from django.conf import settings
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from asgiref.sync import sync_to_async

# --- Django Setup ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_rec.settings')
django.setup()
# --- End Django Setup ---

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Proxy configuration (optional)
PROXY = None

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

async def scrape_jobsearchmalawi():
    print("Current working directory:", os.getcwd())
    base_url = "https://jobsearchmalawi.com/"
    jobs = []
    
    # Set up Selenium
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Commented out for debugging
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7103.94 Safari/537.36")
    if PROXY:
        chrome_options.add_argument(f"--proxy-server={PROXY}")
    
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        # This website doesn't use standard pagination, so we just load the main page
        logger.info(f"Scraping jobsearchmalawi.com page: {base_url}")
        driver.get(base_url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article.job-card, div.job-listing, li.job"))
        )
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # Try multiple selectors for job cards
        job_elements = soup.select("article.job-card") or soup.select("div.job-listing") or soup.find_all("li", class_="job")
        logger.info(f"Found {len(job_elements)} potential job elements on the page")
        if not job_elements:
            logger.error("No job elements found! Check selector or page structure.")
            with open("jobsearchmalawi_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        
        for job_elem in job_elements:
            try:
                # Try multiple selectors for each field
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
                    "source": "jobsearchmalawi.com",
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
            logger.info(f"Saved {inserted} jobs from jobsearchmalawi.com to database")
        else:
            logger.warning("No jobs were scraped from jobsearchmalawi.com to save.")
        return jobs
    
    except Exception as e:
        driver.save_screenshot("jobsearchmalawi_error.png")
        with open("jobsearchmalawi_error_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source if driver else "No driver/page source available.")
        logger.error(f"Selenium scraping failed for jobsearchmalawi.com: {e}")
        return []
    finally:
        if driver:
            driver.save_screenshot("jobsearchmalawi_final.png")
            with open("jobsearchmalawi_final_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            driver.quit()

if __name__ == "__main__":
    asyncio.run(scrape_jobsearchmalawi())