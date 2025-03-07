# TikTok Scraper

This project automates the process of logging into TikTok, extracting user profile URLs, and saving the data into a CSV file.

## Installation and Setup

### Prerequisites

Ensure you have Python installed along with the required dependencies.

1. Clone this repository:
   ```bash
   git clone https://github.com/your-repo/tiktok-scraper.git
   cd tiktok-scraper
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your TikTok credentials by creating a `.env` file (refer to `.env.example`):
   ```env
   TIKTOK_ACCOUNT="your_tiktok_email"
   TIKTOK_PASSWORD="your_tiktok_password"
   ```

## Code Structure

```
/tiktok_scraper
│── main.py               # Main entry script
│── login.py              # Handles TikTok login authentication
│── scrape_url_lists.py   # Extracts user profile URLs
│── tiktok_scraper.py     # Scrapes TikTok profile data
│── helper.py             # Utility functions for processing data
│── .env.example          # Example environment file with credentials
│── README.md             # Project documentation
│── requirements.txt      # Required Python packages
```

## Workflow

The process is orchestrated in `main.py`, which follows these steps:

1. **Login to TikTok:** Uses `login.py` to authenticate using the credentials provided in the `.env` file.
2. **Scrape Video URLs:** Extracts a list of video URLs related to the hastag and stored.
3. **Scrape Comments Data:** Extract the comments for each video
4. **Scrape User Data:** Extract each commenter's profile.
4. **Save to CSV:** The scraped data is stored in a structured CSV file.

To run the scraper, execute:
```bash
python main.py
```

## Login and CAPTCHA Handling

Since TikTok has security measures in place, the login process involves a **manual CAPTCHA verification step**.

1. The script uses **Selenium with undetected_chromedriver** to open the TikTok login page.
2. Your email and password are automatically filled in from the `.env` file.
3. If TikTok requires a CAPTCHA verification:
   - The script **pauses execution** and prompts the user to solve the CAPTCHA manually.
   - The console will display messages guiding the user.
   - The script **continuously checks** if the CAPTCHA has been solved by monitoring URL changes.
4. Once logged in successfully, the script proceeds to scrape data.

⚠️ **Note:** Ensure that your TikTok account is accessible and does not have additional security settings that block automated logins.

## Expected Outputs

1. **Video URLs List (`url_lists/{Your Hashtag}.json`)**  
    The `url_lists` folder will contain JSON files named after hashtags. Each JSON file stores a list of video URLs related to that hashtag.

2. **Final Output CSV (`tiktok_scrapes/{your hashtag}/tiktok_scrape_{Your hashtag}_timestamp.csv`)**  
   The extracted TikTok profile details are saved into the `tiktok_scrapes` directory, organized by hashtags. The CSV includes:
   - Username
   - Followers count
   - Likes count
   - Bio description
   - Other relevant TikTok profile details

## Notes

- Ensure that your TikTok account does not have additional security measures that may block automated logins.
- Use responsibly and comply with TikTok's Terms of Service when scraping data.
- If CAPTCHA verification appears frequently, consider using alternative login methods such as session-based authentication.
