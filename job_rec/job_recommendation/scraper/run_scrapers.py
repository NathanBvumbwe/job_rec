import psycopg2
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging
import asyncio
# from scrape_jobsearchmalawi import scrape_jobsearchmalawi
# from scrape_ntchito import scrape_ntchito
# from scrape_careers import scrape_careersmw
from job_recommendation.scraper.scrape_jobsearchmalawi import scrape_jobsearchmalawi
from job_recommendation.scraper.scrape_ntchito import scrape_ntchito
from job_recommendation.scraper.scrape_careers import scrape_careersmw

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Database connection configuration
DB_CONFIG = {
    "dbname": "jb_recommendation_035817",
    "user": "postgres",
    "password": "21_21_basi",
    "host": "localhost",
    "port": "5433"
}
      
# Initialize database and create table
def init_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255),
                company VARCHAR(255),
                location VARCHAR(255),
                job_type VARCHAR(100),
                date_posted DATE,
                url TEXT,
                source VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check if unique_url constraint exists
        cursor.execute("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'jobs' AND constraint_type = 'UNIQUE' AND constraint_name = 'unique_url'
        """)
        constraint_exists = cursor.fetchone()
        
        if not constraint_exists:
            # Check for duplicates before adding constraint
            cursor.execute("""
                SELECT url, COUNT(*) 
                FROM jobs 
                GROUP BY url 
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            if duplicates:
                logger.warning(f"Cannot add unique_url constraint due to {len(duplicates)} duplicate URLs. Please deduplicate the table.")
                for url, count in duplicates:
                    logger.warning(f"Duplicate URL: {url} ({count} occurrences)")
            else:
                cursor.execute("ALTER TABLE jobs ADD CONSTRAINT unique_url UNIQUE (url)")
                logger.info("Added unique_url constraint to jobs table")
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

async def run_all_scrapers():
    logger.info("Starting all scrapers")
    jobs = []
    
    # Run scrapers sequentially
    try:
        jobs.extend(await scrape_jobsearchmalawi())
        logger.info("Completed jobsearchmalawi.com scraper")
    except Exception as e:
        logger.error(f"jobsearchmalawi.com scraper failed: {e}")
    
    try:
        jobs.extend(await scrape_ntchito())
        logger.info("Completed ntchito.com scraper")
    except Exception as e:
        logger.error(f"ntchito.com scraper failed: {e}")
    
    try:
        jobs.extend(await scrape_careersmw())
        logger.info("Completed careersmw.com scraper")
    except Exception as e:
        logger.error(f"careersmw.com scraper failed: {e}")
    
    logger.info(f"Total jobs scraped: {len(jobs)}")
    return jobs

async def main(run_scheduler=False):
    init_db()
    # Run scrapers immediately
    await run_all_scrapers()
    if run_scheduler:
        # Set up scheduler for daily scraping at 7 AM
        scheduler = AsyncIOScheduler(timezone="Africa/Blantyre")
        scheduler.add_job(run_all_scrapers, "cron", hour=7, minute=0)
        scheduler.start()
        logger.info("Scheduler started for daily scraping at 7 AM CAT")
        # Keep the event loop running
        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
            logger.info("Scheduler shut down")

if __name__ == "__main__":
    # For standalone use, pass True to run_scheduler
    asyncio.run(main(run_scheduler=True))