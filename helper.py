import random
import time
from selenium.webdriver.common.by import By
import json

def scroll_page(driver):
    """
    Scroll the page randomly to mimic human behavior.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.

    Returns:
        None
    """
    scroll_height = driver.execute_script("return document.body.scrollHeight")
    random_scroll = random.randint(1000, scroll_height)
    driver.execute_script(f"window.scrollBy(0, {random_scroll});")
    print(f"Scrolled by {random_scroll}px.")
    random_delay(2, 4)


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


def scroll_element(driver, element_selector):
    """
    Scroll a specific element on the page.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        element_selector (str): CSS selector for the element to scroll
    """
    try:
        # Find the comments container
        container = driver.find_element(By.CSS_SELECTOR, element_selector)
        
        # Get the container's current scroll height
        scroll_height = driver.execute_script("return arguments[0].scrollHeight", container)
        current_scroll = driver.execute_script("return arguments[0].scrollTop", container)
        
        # Scroll by a random amount within the container
        random_scroll = random.randint(500, 1000)  # Smaller increment for comment section
        new_scroll = min(current_scroll + random_scroll, scroll_height)
        
        # Scroll the container
        driver.execute_script("arguments[0].scrollTop = arguments[1]", container, new_scroll)
        print(f"Scrolled container by {random_scroll}px.")
        random_delay(2, 4)
        return True
    except Exception as e:
        print(f"Error scrolling container: {str(e)}")
        return False
    
def load_json(json_file):
    with open(json_file, "r") as f:
        video_urls = json.load(f)
    return video_urls

if __name__ == "__main__":
    urls_output_file = f"urls_lists/_保健品.json"
    video_urls  = load_json(urls_output_file)
    print(video_urls)
