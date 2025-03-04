from tiktok_scraper import TikTokScraper
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        logger.info("Starting TikTok Scraper")
        
        # Get user input
        hashtag = input("Enter the hashtag to scrape (without #): ").strip()
        max_posts = int(input("Enter the maximum number of posts to scrape: ").strip())
        
        logger.info(f"Input parameters - Hashtag: #{hashtag}, Max Posts: {max_posts}")
        
        # Initialize scraper
        scraper = TikTokScraper(headless=False)
        
        # Scrape data
        logger.info(f"Starting to scrape posts with hashtag #{hashtag}")
        results = scraper.scrape_hashtag(hashtag, max_posts)
        
        # Save results
        if results:
            output_file = f"tiktok_scrape_{hashtag}_{time.strftime('%Y%m%d_%H%M%S')}.csv"
            logger.info(f"Saving results to {output_file}")
            scraper.save_to_csv(results, output_file)
        else:
            logger.warning("No results found!")
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        
    finally:
        if 'scraper' in locals():
            scraper.close_driver()