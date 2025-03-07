import json
import os
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import undetected_chromedriver as uc


def get_chrome_driver(user_data_dir=None):
    """
    Sets up a full browser mode undetected Chrome WebDriver.

    Args:
        user_data_dir (str, optional): Path to the Chrome user data directory for maintaining sessions.

    Returns:
        WebDriver: Configured Selenium WebDriver instance.
    """
    options = uc.ChromeOptions()
    options.add_argument("--disable-notifications")  # Disable unnecessary notifications

    if user_data_dir:
        options.add_argument(f"--user-data-dir={user_data_dir}")  # Load user session
        print(f"Using Chrome user data directory: {user_data_dir}")

    # Use undetected ChromeDriver
    print("Running Selenium in undetected full browser mode.")
    return uc.Chrome(options=options)


def random_delay(min_delay=1, max_delay=5):
    """
    Introduce a random delay to mimic human behavior.

    Args:
        min_delay (int): Minimum delay in seconds.
        max_delay (int): Maximum delay in seconds.

    Returns:
        None
    """
    delay = random.uniform(min_delay, max_delay)
    print(f"Sleeping for {round(delay, 2)} seconds...")
    time.sleep(delay)


def scroll_page(driver):
    """
    Scroll the page randomly to mimic human behavior.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.

    Returns:
        None
    """
    scroll_height = driver.execute_script("return document.body.scrollHeight")
    random_scroll = random.randint(100, scroll_height // 2)
    driver.execute_script(f"window.scrollBy(0, {random_scroll});")
    print(f"Scrolled by {random_scroll}px.")
    random_delay(2, 4)

def scrape_tiktok_hashtag_videos(driver, hashtag, max_videos=2000, batch_size=50, rest_seconds=5, user_data_dir=None, retry_delay=2, max_retries=3):
    """
    Scrapes TikTok video URLs from a hashtag page in batches with rest intervals.
    Only refreshes the page if the scroll reaches the bottom and no new videos are loaded.
    """
    # options = webdriver.ChromeOptions()
    # options.add_argument("--disable-notifications")
    # driver = get_chrome_driver(user_data_dir)
    driver.get(f"https://www.tiktok.com/tag/{hashtag}")
    random_delay(5, 10)

    video_urls = []
    last_count = 0
    retry_count = 0

    try:
        while len(video_urls) < max_videos:
            scroll_height = driver.execute_script("return document.body.scrollHeight")
            current_scroll_position = 0

            # Scroll and detect the bottom
            while current_scroll_position < scroll_height:
                current_scroll_position += random.randint(300, 800)  # Mimic a human scroll
                driver.execute_script(f"window.scrollTo(0, {current_scroll_position});")
                print(f"Scrolled to {current_scroll_position}px.")
                random_delay(1, 3)
                scroll_height = driver.execute_script("return document.body.scrollHeight")

            # Check for new videos
            videos = driver.find_elements(By.XPATH, '//a[contains(@href, "/video/")]')
            for video in videos:
                url = video.get_attribute("href")
                if url and url not in video_urls:
                    video_urls.append(url)
                    print(f"Scraped: {url} ({len(video_urls)}/{max_videos})")
                    if len(video_urls) >= max_videos:
                        break

            if len(video_urls) == last_count:
                retry_count += 1
                print(f"No new videos found. Attempt {retry_count}/{max_retries}. Waiting for {retry_delay} seconds...")
                random_delay(retry_delay, retry_delay + 3)
                if retry_count >= max_retries:
                    print("Maximum retries reached. Stopping scraping.")
                    break
                driver.refresh()
                print("Page refreshed. Continuing scraping...")
                random_delay(5, 10)
            else:
                last_count = len(video_urls)

            if len(video_urls) % batch_size == 0:
                print(f"Resting for {rest_seconds} seconds...")
                random_delay(rest_seconds, rest_seconds + 5)

    except Exception as e:
        print(f"Error scraping video URLs: {e}")
    # finally:
    #     driver.quit()

    return video_urls


def append_urls_to_json(new_urls, output_file):
    """
    Appends unique URLs to a JSON file.

    Args:
        new_urls (list): The list of new URLs to append.
        output_file (str): Path to the JSON file.

    Returns:
        None
    """
    # Load existing URLs from the file
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            existing_urls = json.load(f)
    else:
        existing_urls = []

    # Add only unique URLs
    all_urls = list(set(existing_urls + new_urls))

    # Save back to the JSON file
    with open(output_file, "w") as f:
        json.dump(all_urls, f, indent=4)
    print(f"Updated {output_file} with {len(all_urls)} unique URLs.")


