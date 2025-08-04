from django.core.management.base import BaseCommand
import asyncio

# Import the functions you need directly
from job_recommendation.scraper.run_scrapers import main as run_scrapers_main
from job_recommendation.model.test_BERT3 import run_categorization_pipeline
from job_recommendation.model2_reccomender.eish import batch_save_all_matches

class Command(BaseCommand):
    help = 'Runs the full job recommendation pipeline: scrape, categorize, match.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting pipeline...'))

        # 1. Run scrapers
        self.stdout.write('Running scrapers...')
        try:
            awaitable = run_scrapers_main(run_scheduler=False)
            if asyncio.iscoroutine(awaitable):
                asyncio.run(awaitable)
            else:
                awaitable
            self.stdout.write(self.style.SUCCESS('Scraping complete.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Scraping failed: {e}'))
            # Stop the pipeline if scraping fails
            return

        # 2. Categorize jobs (Now called directly)
        self.stdout.write('Categorizing jobs...')
        try:
            run_categorization_pipeline()
            self.stdout.write(self.style.SUCCESS('Categorization complete.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Categorization failed: {e}'))
            # Stop the pipeline if categorization fails
            return

        # 3. Run matching for all users
        self.stdout.write('Matching users to jobs...')
        try:
            batch_save_all_matches(top_n=6)
            self.stdout.write(self.style.SUCCESS('Matching complete.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Matching failed: {e}'))
            return

        self.stdout.write(self.style.SUCCESS('Pipeline finished successfully!'))