import os
from playwright.sync_api import sync_playwright

# Configuration
TARGET_URL = "https://www.1tamilmv.earth/"
OUTPUT_FILE = "movies.txt"

def scrape_movies():
    with sync_playwright() as p:
        # Launching headless browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        print(f"Accessing {TARGET_URL}...")
        try:
            page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"Error loading homepage: {e}")
            browser.close()
            return
        
        # FIX: Get all elements first, then extract HREFs
        # We look for links containing the forum topic pattern
        locator = page.locator('a[href*="/index.php?/forums/topic/"]')
        
        # '.all()' gives us the list of elements found
        link_elements = locator.all()
        
        # Extract the URL strings from the elements
        thread_urls = []
        for link in link_elements:
            try:
                href = link.get_attribute("href")
                if href:
                    thread_urls.append(href)
            except:
                continue
        
        # Remove duplicates from the list
        thread_urls = list(set(thread_urls))
        print(f"Found {len(thread_urls)} movie threads. Checking the top 15...")

        found_magnets = set()
        
        # Limit to top 15 latest threads
        for url in thread_urls[:15]:
            try:
                print(f"Checking: {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Locate the MAGNET button and grab the href attribute directly
                magnet_element = page.locator('a:has-text("MAGNET")').first
                if magnet_element.count() > 0:
                    magnet_link = magnet_element.get_attribute("href")
                    if magnet_link and magnet_link.startswith("magnet:?"):
                        print("  -> Found magnet!")
                        found_magnets.add(magnet_link)
            except Exception as e:
                print(f"  -> Failed to check page: {e}")
                continue

        update_output_file(found_magnets)
        browser.close()

def update_output_file(new_links):
    # Create file if it doesn't exist
    if not os.path.exists(OUTPUT_FILE):
        open(OUTPUT_FILE, 'w').close()
        
    # Read existing links
    with open(OUTPUT_FILE, 'r') as f:
        existing = set(line.strip() for line in f)
    
    # Append only new links
    with open(OUTPUT_FILE, 'a') as f:
        added_count = 0
        for link in new_links:
            if link not in existing:
                f.write(link + "\n")
                added_count += 1
        print(f"Total new links added to {OUTPUT_FILE}: {added_count}")

if __name__ == "__main__":
    scrape_movies()
