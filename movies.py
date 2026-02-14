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
        page.goto(TARGET_URL, wait_until="domcontentloaded")
        
        # Identify movie thread links (look for links containing '/index.php?/forums/topic/')
        # Based on your screenshot, these are the titles under 'Top Releases'
        links = page.locator('a[href*="/index.php?/forums/topic/"]').all_links()
        
        # Use a set to store unique magnets found in this run
        found_magnets = set()
        
        # Limit to top 15 latest threads to save time/resources
        for link in links[:15]:
            try:
                url = link.get_attribute("href")
                page.goto(url, wait_until="domcontentloaded")
                
                # Locate the MAGNET button and grab the href attribute directly
                # This avoids clicking and triggering popups
                magnet_element = page.locator('a:has-text("MAGNET")').first
                if magnet_element.count() > 0:
                    magnet_link = magnet_element.get_attribute("href")
                    if magnet_link and magnet_link.startswith("magnet:?"):
                        found_magnets.add(magnet_link)
            except Exception as e:
                continue

        update_output_file(found_magnets)
        browser.close()

def update_output_file(new_links):
    if not os.path.exists(OUTPUT_FILE):
        open(OUTPUT_FILE, 'w').close()
        
    with open(OUTPUT_FILE, 'r') as f:
        existing = set(line.strip() for line in f)
    
    with open(OUTPUT_FILE, 'a') as f:
        added_count = 0
        for link in new_links:
            if link not in existing:
                f.write(link + "\n")
                added_count += 1
        print(f"Added {added_count} new links.")

if __name__ == "__main__":
    scrape_movies()
