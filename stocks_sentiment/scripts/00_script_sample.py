"""
Simple script to scrape economic calendar table with "show more" functionality.
Auto-downloads ChromeDriver using webdriver-manager.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import sys

def scrape_economic_calendar(url):
    """Scrape economic calendar table by clicking 'show more' until all data loads."""
    
    # Setup Chrome driver with anti-detection measures
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Add user agent to look more like a real browser
    options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    print("Setting up ChromeDriver (this may download it if needed)...")
    try:
        # Auto-install ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(60)
        print("✓ Chrome driver initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize Chrome driver: {e}")
        print("\nMake sure Chrome browser is installed!")
        sys.exit(1)
    
    try:
        print(f"\nLoading page: {url}")
        driver.get(url)
        
        # Debug info
        print(f"Page title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        
        time.sleep(5)  # Initial page load
        
        # Wait for the table to actually load
        try:
            print("Waiting for table to load...")
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "eventHistoryTable320"))
            )
            print("✓ Table found!")
        except TimeoutException:
            print("✗ Table not found after 20 seconds")
            print("Taking screenshot for debugging...")
            driver.save_screenshot("debug_screenshot.png")
            print("Screenshot saved as debug_screenshot.png")
            
            # Try to find any tables on the page
            tables = driver.find_elements(By.TAG_NAME, "table")
            print(f"Found {len(tables)} tables on the page")
            
            # Check if there's a CAPTCHA or block message
            if "captcha" in driver.page_source.lower() or "access denied" in driver.page_source.lower():
                print("\n⚠️  WARNING: The site may be blocking automated access")
                print("Check debug_screenshot.png to see what's displayed")
            
            raise
        
        # Click "show more" button repeatedly
        max_clicks = 50  # Safety limit
        clicks = 0
        consecutive_failures = 0
        
        print("\n" + "="*50)
        print("Starting to click 'show more' buttons...")
        print("="*50)
        
        while clicks < max_clicks:
            try:
                # Common selectors for "show more" buttons on economic calendars
                selectors = [
                    "a.showMoreHistoryBtn",
                    "a#showMoreHistory320",
                    "a[onclick*='showMore']",
                    ".show-more-link",
                    "//a[contains(text(), 'Show more')]",
                    "//a[contains(@class, 'showMore')]",
                ]
                
                button_found = False
                for selector in selectors:
                    try:
                        # Use XPath for text-based search
                        if selector.startswith("//"):
                            button = driver.find_element(By.XPATH, selector)
                        else:
                            button = driver.find_element(By.CSS_SELECTOR, selector)
                        
                        if button.is_displayed() and button.is_enabled():
                            # Scroll to button
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                            time.sleep(0.5)
                            
                            # Try to click it
                            try:
                                button.click()
                            except:
                                # If regular click fails, try JavaScript click
                                driver.execute_script("arguments[0].click();", button)
                            
                            clicks += 1
                            consecutive_failures = 0
                            print(f"✓ Clicked 'show more' {clicks} times")
                            time.sleep(1.5)  # Wait for content to load
                            button_found = True
                            break
                    except Exception as e:
                        continue
                
                if not button_found:
                    consecutive_failures += 1
                    if consecutive_failures > 2:
                        print("✓ No more 'show more' button found (tried 3 times)")
                        break
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Finished loading after {clicks} clicks")
                break
        
        # Extract the table
        print("\n" + "="*50)
        print("Extracting table data...")
        print("="*50)
        
        table = driver.find_element(By.ID, "eventHistoryTable320")
        
        # Get headers
        headers = []
        for th in table.find_elements(By.CSS_SELECTOR, "thead th"):
            header_text = th.text.strip()
            if header_text:  # Only add non-empty headers
                headers.append(header_text)
        
        print(f"Headers: {headers}")
        
        # Get all rows
        rows = []
        for tr in table.find_elements(By.CSS_SELECTOR, "tbody tr"):
            row = []
            for td in tr.find_elements(By.TAG_NAME, "td"):
                row.append(td.text.strip())
            if row:
                rows.append(row)
        
        print(f"✓ Extracted {len(rows)} rows")
        
        # Create DataFrame - handle case where headers might be shorter than row data
        if rows:
            if len(headers) < len(rows[0]):
                # Pad headers if needed
                while len(headers) < len(rows[0]):
                    headers.append(f"Column_{len(headers)}")
            
            df = pd.DataFrame(rows, columns=headers[:len(rows[0])])
        else:
            print("⚠️  No rows found in table!")
            df = pd.DataFrame()
        
        return df
        
    except Exception as e:
        print(f"\n{'='*50}")
        print(f"ERROR: {e}")
        print("="*50)
        print("Attempting to save page source for debugging...")
        try:
            with open("page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("✓ Page source saved to page_source.html")
        except:
            print("✗ Could not save page source")
        raise
        
    finally:
        print("\nClosing browser...")
        driver.quit()


if __name__ == "__main__":
    # Replace with your actual URL
    URL = "https://www.investing.com/economic-calendar/michigan-consumer-sentiment-320"
    
    print("="*50)
    print("WEB SCRAPER FOR ECONOMIC CALENDAR")
    print("="*50)
    
    try:
        df = scrape_economic_calendar(URL)
        
        if df.empty:
            print("\n⚠️  WARNING: DataFrame is empty!")
            sys.exit(1)
        
        # Save to CSV
        output_path = "stocks_sentiment/data/raw/umcsent.csv"
        df.to_csv(output_path, index=False)
        
        print(f"\n{'='*50}")
        print(f"✓ SUCCESS!")
        print(f"{'='*50}")
        print(f"Saved to: {output_path}")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print("\nFirst 5 rows:")
        print(df.head())
        print("\nLast 5 rows:")
        print(df.tail())
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n{'='*50}")
        print(f"✗ FAILED: {e}")
        print(f"{'='*50}")
        print("\nCheck debug_screenshot.png and page_source.html for clues")
        sys.exit(1)