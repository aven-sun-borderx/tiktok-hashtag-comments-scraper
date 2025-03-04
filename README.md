# TikTok Scraper

## Overview
This project is a **TikTok Scraper** built using Python and Selenium. It allows users to scrape TikTok user profiles, post comments, and hashtag-based posts efficiently. The scraped data is stored in structured folders for better organization.

## Features
✅ Scrapes TikTok user profiles for bio, contact details (email, WhatsApp, phone), and links.  
✅ Extracts comments from TikTok posts, including replies and user details.  
✅ Collects posts based on hashtags, scraping both post details and comments.  
✅ Saves all extracted data into structured folders based on hashtags with timestamped CSV files.

## Installation
### Prerequisites
- Python 3.x
- Google Chrome installed
- ChromeDriver (managed by `webdriver-manager`)

### Install Dependencies
Run the following command to install required dependencies:
```bash
pip install selenium webdriver-manager beautifulsoup4
```

## Usage
### Running the Scraper
To start scraping TikTok data, run:
```bash
python main.py
```
You will be prompted to enter the hashtag and the maximum number of posts to scrape.

### Expected Output Structure
Scraped data is saved in the `tiktok_scrapes/` directory, with subdirectories for each hashtag. Example structure:
```
tiktok_scrapes/
│── dancechallenge/
│   ├── tiktok_data_dancechallenge_20250303_120102.csv
│   ├── tiktok_data_dancechallenge_20250304_130504.csv
│── funnyvideos/
│   ├── tiktok_data_funnyvideos_20250303_121500.csv
│── travelvlogs/
│   ├── tiktok_data_travelvlogs_20250305_140830.csv
```

## Code Structure
```
├── tiktok_scraper.py    # Main scraper logic
├── main.py              # CLI interface for running scraper
├── requirements.txt     # List of dependencies
├── README.md            # Project documentation
```

## Functions
### **`scrape_user_profile(username)`**
Scrapes a TikTok user's profile, extracting bio, contact info, and links.

### **`enhanced_scrape_comments(post_url, max_comments=50)`**
Extracts comments from a TikTok post, handling nested replies and parent comments.

### **`scrape_hashtag(hashtag, max_posts=10, batch_size=3)`**
Scrapes TikTok posts under a given hashtag and extracts post details, comments, and user profiles.

### **`save_to_csv(data, filename)`**
Saves scraped data into CSV format within structured hashtag-based folders.

## Troubleshooting
### **Common Issues & Fixes**
- **`selenium.common.exceptions.TimeoutException`**: Increase `WebDriverWait` time in `_init_driver()`.
- **Scraper doesn't find elements**: TikTok updates its UI frequently. Update CSS selectors in `scrape_user_profile` and `enhanced_scrape_comments`.
- **Headless mode issues**: Run with `headless=False` for debugging:
  ```python
  scraper = TikTokScraper(headless=False)
  ```

## License
This project is licensed under the MIT License.

## Author
Yi Sun (Aven)
