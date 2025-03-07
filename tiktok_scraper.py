import time
import csv
import random
import logging
from turtle import pos
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
from datetime import datetime
import os
import time
from helper import scroll_page
from scrape_url_lists import get_chrome_driver

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
class TikTokScraper:
    def __init__(self, driver):
        """
        Initializes the TikTok scraper.
        :param headless: If True, runs Chrome in headless mode.
        """
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)
        logger.info("TikTok Scraper initialized successfully")

    def _extract_contact_info(self, text):
        """Extract contact information from text using regex patterns"""
        logger.debug(f"Extracting contact information from text: {text[:100]}...")
        contact_info = {
            'email': '',
            'whatsapp': '',
            'phone': ''
        }
        
        # Email pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_match = re.search(email_pattern, text)
        if email_match:
            contact_info['email'] = email_match.group()
            logger.info(f"Found email: {contact_info['email']}")
            
        # WhatsApp pattern (various formats)
        whatsapp_patterns = [
            r'wa\.me/\d+',
            r'whatsapp\.com/\d+',
            r'WhatsApp:?\s*[+]?\d+',
            r'WA:?\s*[+]?\d+'
        ]
        for pattern in whatsapp_patterns:
            whatsapp_match = re.search(pattern, text)
            if whatsapp_match:
                contact_info['whatsapp'] = whatsapp_match.group()
                logger.info(f"Found WhatsApp: {contact_info['whatsapp']}")
                break
                
        # Phone pattern
        phone_pattern = r'(?:(?:\+|00)[1-9]\d{0,3}[\s.-]?)?(?:\d{1,4}[\s.-]?){1,4}\d{4}'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            contact_info['phone'] = phone_match.group()
            logger.info(f"Found phone: {contact_info['phone']}")
            
        return contact_info

    def scrape_user_profile(self, username):
        """
        Scrapes a user's TikTok profile for contact information
        """
        logger.info(f"Starting to scrape profile for user: {username}")
        try:
            profile_url = f"https://www.tiktok.com/@{username}"
            logger.debug(f"Navigating to profile URL: {profile_url}")
            self.driver.get(profile_url)
            time.sleep(1)

            profile_data = {
                'username': username,
                'bio': '',
                'email': '',
                'whatsapp': '',
                'phone': '',
                'links': []
            }

            # Wait for profile content to load
            try:
                logger.debug("Waiting for bio element to load")
                bio_element = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-e2e="user-bio"]'))
                )
                profile_data['bio'] = bio_element.text.strip()
                logger.info(f"Found bio for user {username}")
            except Exception as e:
                logger.warning(f"Bio not found for user {username}: {str(e)}")

            # Get page source after dynamic content loads
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Extract all links
            links = soup.find_all('a')
            for link in links:
                href = link.get('href', '')
                if href and not href.startswith(('javascript:', '#')):
                    profile_data['links'].append(href)
                    logger.debug(f"Found link: {href}")

            # Extract contact information from bio
            if profile_data['bio']:
                logger.debug("Extracting contact information from bio")
                contact_info = self._extract_contact_info(profile_data['bio'])
                profile_data.update(contact_info)

            logger.info(f"Successfully scraped profile for user {username}")
            return profile_data

        except Exception as e:
            logger.error(f"Error scraping profile for {username}: {str(e)}", exc_info=True)
            return None

    def scrape_comments(self, post_url, max_comments=10000):
        """
        Scrapes comments from a TikTok post using updated selectors.
        Monitors URL changes while scrolling to detect navigation away from the post.
        """
        logger.info(f"Starting to scrape comments from post: {post_url}")
        comments_data = []
        post_url = str(post_url)
        try:
            self.driver.get(post_url)
            logger.info(f"Get the post url: {post_url}")
            time.sleep(2)  # Wait for initial load
            original_url = self.driver.current_url
            logger.info(f"Original url: {original_url}")

            scroll_attempts = 0
            max_scroll_attempts = 10000  # Increased to allow for more scrolling
            no_new_comments_count = 0
            prev_comment_count = 0

            # Updated comment container selectors based on TikTok's HTML structure
            comment_container_selectors = [
                'div[class*="DivCommentContentWrapper"]',
                'div[class*="css-1bkazzl-DivCommentContentWrapper"]',
                'div[class*="DivCommentObjectWrapper"]'
            ]

            # Wait for comments to load
            try:
                for selector in comment_container_selectors:
                    try:
                        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        logger.info(f"Comment container found using selector: {selector}")
                        break
                    except:
                        continue
            except Exception as e:
                logger.warning(f"Timeout waiting for comments to load: {str(e)}")
                return comments_data

            while len(comments_data) < max_comments and scroll_attempts < max_scroll_attempts:
                # Check if we've navigated away from the original post
                current_url = self.driver.current_url
                if current_url != original_url:
                    logger.warning(f"URL changed from {original_url} to {current_url}. Stopping comment collection.")
                    break
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Find comment containers using multiple selectors
                comment_containers = []
                for selector in comment_container_selectors:
                    containers = soup.select(selector)
                    if containers:
                        comment_containers = containers
                        break

                for container in comment_containers:
                    try:
                        # Updated username selectors
                        username_selectors = [
                            'div[class*="DivUsernameContentWrapper"] a[href*="/@"]',
                            'a[class="link-diy-focus"]',
                            'div[class*="css-1c5c5rm-DivCommentHeaderWrapper"] a',
                            'div[class*="DivCardAvatar"] p[class*="user-name"]',
                            'div[class*="DivCardAvatar"] h4[class*="UserTitle"] p',
                            'div[class*="DivCardAvatar"] a[title]'
                        ]
                        
                        username = None
                        for selector in username_selectors:
                            username_elem = container.select_one(selector)
                            if username_elem:
                                href = username_elem.get('href', '')
                                if '/@' in href:
                                    username = href.split('/@')[1].split('?')[0]
                                elif selector.endswith('[title]'):
                                    username = username_elem.get('title')
                                else:
                                    username = username_elem.text
                                if username and username.strip():
                                    username = username.strip()
                                    logger.info(f"Found comments author: {username}")
                                    break

                        # Updated comment text selectors to handle nested levels
                        comment_text = None
                        comment_level = None
                        parent_comment = None
                        
                        # First try to find the comment level
                        for level in range(1, 10):  # Check up to 10 levels deep
                            level_selector = f'span[data-e2e="comment-level-{level}"]'
                            comment_elem = container.select_one(level_selector)
                            if comment_elem:
                                comment_text = comment_elem.get_text(strip=True)
                                comment_level = level
                                
                                # If it's a reply (level > 1), try to find the parent comment
                                if level > 1:
                                    try:
                                        # Look for parent container
                                        parent_container = container.find_previous_sibling('div', {'class': lambda x: x and 'DivCommentContentWrapper' in x})
                                        if parent_container:
                                            parent_username_elem = parent_container.select_one('div[class*="DivUsernameContentWrapper"] a[href*="/@"]')
                                            if parent_username_elem:
                                                parent_href = parent_username_elem.get('href', '')
                                                if '/@' in parent_href:
                                                    parent_comment = parent_href.split('/@')[1].split('?')[0]
                                    except Exception as e:
                                        logger.debug(f"Error finding parent comment: {str(e)}")
                                break

                        # If no comment found with level attribute, try fallback selectors
                        if not comment_text:
                            fallback_selectors = [
                                'span[class*="TUXText"][class*="StyledTUXText"]',
                                'div[class*="DivCommentContentSplitWrapper"] span[class*="TUXText"]',
                                'p[class*="TUXText TUXText--tiktok-sans TUXText--weight-medium"]'
                            ]
                            
                            for selector in fallback_selectors:
                                comment_elem = container.select_one(selector)
                                if comment_elem:
                                    comment_text = comment_elem.get_text(strip=True)
                                    comment_level = 1  # Assume top level if we can't determine
                                    break

                        if username and comment_text:
                            comment_data = {
                                'username': username,
                                'comment_text': comment_text,
                                'comment_level': comment_level,
                                'parent_comment': parent_comment
                            }
                            
                            if comment_data not in comments_data:
                                comments_data.append(comment_data)
                                logger.info(f"Added level {comment_level} comment from {username}: {comment_text[:50]}...")
                    
                    except Exception as e:
                        logger.error(f"Error processing comment: {str(e)}")
                        continue

                if len(comments_data) < max_comments:
                    try:
                        # Scroll with a larger increment and add some randomization
                        current_scroll = self.driver.execute_script("return window.pageYOffset;")
                        scroll_amount = random.randint(800, 1200)  # Randomize scroll amount
                        self.driver.execute_script(f"window.scrollTo(0, {current_scroll + scroll_amount});")
                        
                        # Add a small random delay to seem more human-like
                        time.sleep(random.uniform(2, 4))
                        
                        # Scroll up slightly to trigger potential lazy loading
                        self.driver.execute_script(f"window.scrollTo(0, {current_scroll + scroll_amount - 100});")
                        time.sleep(1)
                    except Exception as e:
                        logger.error(f"Error scrolling page: {str(e)}")
                
                scroll_attempts += 1
                
                # Check URL again after scrolling
                current_url = self.driver.current_url
                if current_url != original_url:
                    logger.warning(f"URL changed after scrolling from {original_url} to {current_url}. Stopping comment collection.")
                    break

                if prev_comment_count == len(comments_data):
                    no_new_comments_count += 1
                else:
                    no_new_comments_count = 0
                    prev_comment_count = len(comments_data)

                # Increase tolerance for no new comments
                if no_new_comments_count >= 5:
                    logger.info("No new comments found after multiple scroll attempts. Stopping...")
                    break

            logger.info(f"Finished scraping comments. Found {len(comments_data)} comments after {scroll_attempts} scroll attempts")
            return comments_data
            
        except Exception as e:
            logger.error(f"Error scraping comments: {str(e)}")
            return comments_data

    def scrape_hashtag(self, hashtag, video_url_list, batch_size=1, output_file=None):
        """
        Scrapes TikTok posts with a specific hashtag and their comments
        
        Args:
            hashtag (str): The hashtag to search for (without the # symbol)
            max_posts (int): Maximum number of posts to scrape
            batch_size (int): Number of posts to process in each batch to avoid memory issues
        
        Returns:
            list: List of dictionaries containing post data, comments, and profile information
        """
        logger.info(f"Starting to scrape hashtag: #{hashtag}")
        processed_urls = set()
        
        try:
            # Process videos in batches to manage memory and allow for partial success
            for i, video_url in enumerate(video_url_list):
                video_results = []
                try:
                    self.driver.execute_script("return document.readyState")  # Check if the session is still active
                except:
                    logger.error("WebDriver session expired. Restarting driver...")
                    self.driver.quit()
                    self.driver = get_chrome_driver()
                    time.sleep(3)

                logger.info(f"Processing video {i+1} of {len(video_url_list)}")
                
                try:
                    if video_url in processed_urls:
                        logger.info(f"Skipping already processed video: {video_url}")
                        continue
                        
                    logger.info(f"Processing video: {video_url}")
                    
                    # Get comments for this video
                    comments = self.scrape_comments(video_url)
                    logger.info(f"Found {len(comments)} comments")
                    
                    # Extract username from URL or first comment
                    username = None
                    if comments and len(comments) > 0:
                        username = comments[0].get('username')
                    
                    # Process each comment and get commenter profiles
                    for comment in comments:
                        commenter_username = comment['username']
                        
                        # Get commenter's profile information
                        try:
                            profile_info = self.scrape_user_profile(commenter_username)
                        except Exception as e:
                            logger.error(f"Error getting profile for {commenter_username}: {str(e)}")
                            profile_info = {}
                        
                        # Combine all information
                        result = {
                            'hashtag': hashtag,
                            'post_url': video_url,
                            'post_author': username,
                            'commenter_username': commenter_username,
                            'comment_text': comment['comment_text'],
                            'comment_level': comment['comment_level'],
                            'parent_comment': comment['parent_comment'],
                            'commenter_bio': profile_info.get('bio', ''),
                            'commenter_contact': {
                                'email': profile_info.get('email', ''),
                                'whatsapp': profile_info.get('whatsapp', ''),
                                'phone': profile_info.get('phone', '')
                            },
                            'commenter_links': profile_info.get('links', [])
                        }
                        
                        video_results.append(result)
                        
                    processed_urls.add(video_url)
                    logger.info(f"Successfully processed video: {video_url}")
                    
                except Exception as e:
                    logger.error(f"Error processing video {video_url}: {str(e)}")
                    continue
                
                # Save results after each batch
                if video_results:
                    logger.info(f"Saving results to {output_file}")
                    self.save_to_csv(video_results, output_file)
                    logger.info(f"Saved {len(video_results)} results so far")
        except Exception as e:
            logger.error(f"Error scraping hashtag: {str(e)}")
            return 

    def save_to_csv(self, data, filename="tiktok_data.csv"):
        """
        Saves scraped data to a CSV file within a structured folder and appends new data.
        """
        if not data:
            logger.warning("No data to save")
            return

        try:
            # Define all possible fields including flattened nested dictionaries
            fieldnames = [
                'hashtag',
                'post_url',
                'post_author',
                'commenter_username',
                'comment_text',
                'comment_level',
                'parent_comment',
                'commenter_bio',
                'commenter_email',
                'commenter_whatsapp',
                'commenter_phone',
                'commenter_links'
            ]

            # Get the hashtag name from the first entry in the data
            hashtag = data[0].get('hashtag', 'unknown_hashtag')
            hashtag_folder = f"tiktok_scrapes/{hashtag}"

            # Create the directory if it doesn't exist
            os.makedirs(hashtag_folder, exist_ok=True)

            # Generate filename
            filepath = os.path.join(hashtag_folder, filename)

            # Check if file exists to decide whether to write headers
            file_exists = os.path.isfile(filepath)

            # Open file in append mode ('a') to keep adding new data
            with open(filepath, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                # Write headers only if the file does not already exist
                if not file_exists:
                    writer.writeheader()

                # Flatten nested dictionaries
                flattened_data = []
                for item in data:
                    flat_item = {
                        'hashtag': item.get('hashtag', ''),
                        'post_url': item.get('post_url', ''),
                        'post_author': item.get('post_author', ''),
                        'commenter_username': item.get('commenter_username', ''),
                        'comment_text': item.get('comment_text', ''),
                        'comment_level': item.get('comment_level', ''),
                        'parent_comment': item.get('parent_comment', ''),
                        'commenter_bio': item.get('commenter_bio', ''),
                        'commenter_email': item.get('commenter_contact', {}).get('email', ''),
                        'commenter_whatsapp': item.get('commenter_contact', {}).get('whatsapp', ''),
                        'commenter_phone': item.get('commenter_contact', {}).get('phone', ''),
                        'commenter_links': '|'.join(item.get('commenter_links', [])) if item.get('commenter_links') else ''
                    }
                    flattened_data.append(flat_item)

                # Append new data to CSV
                writer.writerows(flattened_data)

                logger.info(f"Appended {len(flattened_data)} records to {filepath}")

        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")


    def close_driver(self):
        """
        Closes the Selenium WebDriver
        """
        logger.info("Closing web driver")
        self.driver.quit()
        logger.info("Web driver closed successfully")
