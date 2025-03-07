import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def wait_for_human_captcha(driver):
    """
    Waits for the user to complete the CAPTCHA manually before continuing.
    Detects successful login by checking if the profile picture appears.
    """
    print("CAPTCHA detected! Please complete the CAPTCHA manually in the browser.")
    
    # Store the initial login URL
    login_url = driver.current_url

    while True:
        try:
            if driver.current_url != login_url:
                print(f"URL changed to {driver.current_url}. Login successful!")
                break
            print("Still on the login page, waiting for CAPTCHA completion... (Checking every 5 seconds)")
            time.sleep(5)  # Check every 5 seconds
        except:
            print("Waiting for CAPTCHA to be solved... (Checking every 5 seconds)")
            time.sleep(5)  # Wait before checking again


def login_tiktok(driver, account, password):
    """
    Logs into TikTok with the given username and password.

    Args:
        driver: Selenium WebDriver instance.
        username: TikTok account username.
        password: TikTok account password.

    Returns:
        None
    """
    driver.get("https://www.tiktok.com/login")
    time.sleep(5)  # Wait for the page to load

    # Switch to the login iframe if needed
    try:
        iframe = driver.find_element(By.TAG_NAME, "iframe")
        driver.switch_to.frame(iframe)
        time.sleep(2)
    except:
        print("No iframe detected, continuing.")

    # Click on "Use phone / email / username"
    try:
        login_button = driver.find_element(By.XPATH, "//div[contains(text(), 'Use phone / email / username')]")
        login_button.click()
        time.sleep(3)
    except Exception as e:
        print(f"Error finding login button: {e}")
        return False

    # Click "Log in with Email / Username"
    try:
        email_tab = driver.find_element(By.XPATH, "//a[contains(@href, '/login/phone-or-email')]")
        email_tab.click()
        time.sleep(2)
    except Exception as e:
        print(f"Error finding email tab: {e}")
        return False
    
    print("Finding email button sucessfully!")

    # Enter username
    username_input = driver.find_element(By.NAME, "username")
    print("Finding username button sucessfully!")
    username_input.send_keys(account)
    time.sleep(1)
    print("Enter username sucessfully!")

    # Enter password
    password_input = driver.find_element(By.XPATH, "//input[@type='password' and @placeholder='Password']")
    password_input.send_keys(password)
    print("Enter password sucessfully!")
    # Press Enter or click the login button
    password_input.send_keys(Keys.RETURN)
    time.sleep(5)  # Wait for TikTok to log in

    

    # Check if login was successful
    try:
        wait_for_human_captcha(driver)
        print("Login successful!")
        # return True
    except:
        print("Login may have failed. Check credentials or CAPTCHA.")
        # return False
