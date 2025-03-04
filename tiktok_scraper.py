import time
import csv
import random
import logging
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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
class TikTokScraper:
    def __init__(self, headless=True):
        """
        Initializes the TikTok scraper.
        :param headless: If True, runs Chrome in headless mode.
        """
        self.headless = headless
        logger.info("Initializing TikTok Scraper")
        self.driver = self._init_driver()
        self.wait = WebDriverWait(self.driver, 10)
        logger.info("TikTok Scraper initialized successfully")

    def _init_driver(self):
        """
        Initializes the Selenium WebDriver with options.
        """
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("start-maximized")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 110)}.0.0.0 Safari/537.36")

        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

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

    def _save_debug_html(self, html, prefix='debug'):
        """Save HTML content to a file for debugging"""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{timestamp}.html"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"Saved debug HTML to {filename}")
        except Exception as e:
            logger.error(f"Failed to save debug HTML: {str(e)}")

    def scrape_user_profile(self, username):
        """
        Scrapes a user's TikTok profile for contact information
        """
        logger.info(f"Starting to scrape profile for user: {username}")
        try:
            profile_url = f"https://www.tiktok.com/@{username}"
            logger.debug(f"Navigating to profile URL: {profile_url}")
            self.driver.get(profile_url)
            time.sleep(3)

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

    def scrape_comments(self, post_url, max_comments=50):
        """
        Scrapes comments from a TikTok post using updated selectors.
        Monitors URL changes while scrolling to detect navigation away from the post.
        """
        logger.info(f"Starting to scrape comments from post: {post_url}")
        try:
            self.driver.get(post_url)
            time.sleep(5)  # Wait for initial load
            
            original_url = self.driver.current_url
            comments_data = []
            scroll_attempts = 0
            max_scroll_attempts = 15  # Increased to allow for more scrolling

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
                                    logger.info(f"Found post author: {username}")
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
                        # If comment section not found, try scrolling the whole page
                        current_scroll = self.driver.execute_script("return window.pageYOffset;")
                        self.driver.execute_script(f"window.scrollTo(0, {current_scroll + 600});")
                        time.sleep(2)
                    except Exception as e:
                        logger.error(f"Error scrolling page: {str(e)}")
                
                scroll_attempts += 1
                
                # Check URL again after scrolling
                current_url = self.driver.current_url
                if current_url != original_url:
                    logger.warning(f"URL changed after scrolling from {original_url} to {current_url}. Stopping comment collection.")
                    break

            logger.info(f"Finished scraping comments. Found {len(comments_data)} comments after {scroll_attempts} scroll attempts")
            return comments_data
            
        except Exception as e:
            logger.error(f"Error scraping comments: {str(e)}")
            return comments_data

    def scrape_hashtag(self, hashtag, max_posts=10, batch_size=3):
        """
        Scrapes TikTok posts with a specific hashtag and their comments
        
        Args:
            hashtag (str): The hashtag to search for (without the # symbol)
            max_posts (int): Maximum number of posts to scrape
            batch_size (int): Number of posts to process in each batch to avoid memory issues
        
        Returns:
            list: List of dictionaries containing post data, comments, and profile information
        """
        logger.info(f"Starting to scrape hashtag: #{hashtag}, max posts: {max_posts}")
        all_results = []
        processed_urls = set()  # Keep track of processed URLs to avoid duplicates
        
        try:
            # First collect all video URLs through scrolling
            url = f"https://www.tiktok.com/tag/{hashtag}"
            self.driver.get(url)
            time.sleep(5)  # Wait for initial load
            
            video_urls = []
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scroll_attempts = 100  # Prevent infinite scrolling
            
            while len(video_urls) < max_posts and scroll_attempts < max_scroll_attempts:
                # Find all video links on current page
                url_selectors = [
                    'a[href*="/video/"]',
                    'a[data-e2e*="video-link"]',
                    'div[class*="DivWrapper"] a'
                ]
                
                for selector in url_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        try:
                            video_url = elem.get_attribute('href')
                            if video_url and video_url not in processed_urls:
                                video_urls.append(video_url)
                                logger.info(f"Found video URL: {video_url}, Total found: {len(video_urls)}")
                                if len(video_urls) >= max_posts:
                                    break
                        except Exception as e:
                            logger.debug(f"Error getting URL from element: {str(e)}")
                            continue
                    
                    if len(video_urls) >= max_posts:
                        break
                
                # Scroll down to load more videos
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Wait for new content to load
                
                # Check if we've reached the bottom
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_attempts += 1
                    logger.debug(f"No new content loaded, attempt {scroll_attempts}/{max_scroll_attempts}")
                else:
                    scroll_attempts = 0  # Reset counter if we found new content
                last_height = new_height
            
            logger.info(f"Found {len(video_urls)} video URLs")
            
            # Process videos in batches to manage memory and allow for partial success
            for i in range(0, len(video_urls), batch_size):
                batch = video_urls[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}, videos {i+1} to {min(i+batch_size, len(video_urls))}")
                
                for video_url in batch:
                    try:
                        if video_url in processed_urls:
                            continue
                            
                        logger.info(f"Processing video: {video_url}")
                        
                        # Get comments for this video
                        comments = self.scrape_comments(video_url)
                        logger.info(f"Found {len(comments)} comments")
                        
                        # Extract username from URL or first comment
                        username = None
                        if comments and len(comments) > 0:
                            username = comments[0].get('username')
                        
                        # Get video author's profile if username was found
                        author_profile = None
                        if username:
                            author_profile = self.scrape_user_profile(username)
                        
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
                                # 'author_bio': author_profile.get('bio', '') if author_profile else '',
                                # 'author_contact': {
                                #     'email': author_profile.get('email', ''),
                                #     'whatsapp': author_profile.get('whatsapp', ''),
                                #     'phone': author_profile.get('phone', '')
                                # } if author_profile else {},
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
                            
                            all_results.append(result)
                            
                        processed_urls.add(video_url)
                        logger.info(f"Successfully processed video: {video_url}")
                        
                    except Exception as e:
                        logger.error(f"Error processing video {video_url}: {str(e)}")
                        continue
                
                # Save intermediate results after each batch
                if all_results:
                    self.save_to_csv(all_results, f"tiktok_data_{hashtag}_intermediate.csv")
                    logger.info(f"Saved intermediate results, {len(all_results)} entries so far")
            
            logger.info(f"Finished scraping hashtag #{hashtag}. Found {len(all_results)} results")
            return all_results
            
        except Exception as e:
            logger.error(f"Error scraping hashtag: {str(e)}")
            # Save any results we got before the error
            if all_results:
                self.save_to_csv(all_results, f"tiktok_data_{hashtag}_error_recovery.csv")
                logger.info(f"Saved {len(all_results)} results before error")
            return all_results

    def save_to_csv(self, data, filename="tiktok_data.csv"):
        """
        Saves scraped data to a CSV file within a structured folder.
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

            # Generate filename with timestamp
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filepath = os.path.join(hashtag_folder, f"tiktok_data_{hashtag}_{timestamp}.csv")

            # Flatten nested dictionaries in the data
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

            # Save to CSV file
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flattened_data)

            logger.info(f"Data saved to {filepath}")

        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")

    def close_driver(self):
        """
        Closes the Selenium WebDriver
        """
        logger.info("Closing web driver")
        self.driver.quit()
        logger.info("Web driver closed successfully")
