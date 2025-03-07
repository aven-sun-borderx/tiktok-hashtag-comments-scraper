from tiktok_scraper import TikTokScraper
import logging
import time
from scrape_url_lists import scrape_tiktok_hashtag_videos, append_urls_to_json, get_chrome_driver
from dotenv import load_dotenv
import os
from login import login_tiktok
from helper import load_json

load_dotenv(dotenv_path=".env") 
Tiktok_account = os.getenv("TIKTOK_ACCOUNT")
Tiktok_password = os.getenv("TIKTOK_PASSWORD")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"{Tiktok_account}: {Tiktok_password}")

if __name__ == "__main__":
    try:
        logger.info("Starting TikTok Scraper")
        
        # Get user input
        hashtag = input("Enter the hashtag to scrape (without #): ").strip()
        max_videos = int(input("Enter the maximum number of posts to scrape: ").strip())
        output_file = f"tiktok_scrape_{hashtag}_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        urls_output_file = f"urls_lists/{hashtag}.json"

        logger.info(f"Input parameters - Hashtag: #{hashtag}, Max Posts: {max_videos}")
        logger.info("Trying to login...")
        driver = get_chrome_driver()

        # Login to Tiktok
        login_tiktok(driver, Tiktok_account, Tiktok_password)

        # Start by sraping the url list
        video_urls = scrape_tiktok_hashtag_videos(
            driver, hashtag, max_videos=max_videos, batch_size=50, rest_seconds=5, user_data_dir=None, retry_delay=2, max_retries=1 
        )

        # Append the URLs to the JSON file
        append_urls_to_json(video_urls, urls_output_file)
        
        # Initialize scraper
        scraper = TikTokScraper(driver=driver)
        
        # Scrape data
        logger.info(f"Starting to scrape posts with hashtag #{hashtag}")

        # load the urls first
        video_urls = load_json(urls_output_file)
        scraper.scrape_hashtag(hashtag, video_urls, batch_size=3, output_file=output_file)
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        
    finally:
        if 'scraper' in locals():
            scraper.close_driver()