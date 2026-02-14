import os
import re
from playwright.sync_api import sync_playwright

# Configuration
TARGET_URL = "https://www.1tamilmv.earth/"
OUTPUT_FILE = "movies.txt"

def get_language_group(title):
    # Normalize title for checking
    t_lower = title.lower()
    
    # Check for explicit "Multi" tag or multiple audio languages
    languages = ["Tamil", "Telugu", "Hindi", "Malayalam", "Kannada", "English"]
    found_langs = [lang for lang in languages if lang.lower() in t_lower]
    
    # If "Multi" keyword is present OR more than 1 language is found (e.g., Tamil + Telugu)
    if "multi" in t_lower or len(found_langs) > 1:
        return "Multi"
    elif len(found_langs) == 1:
        return found_langs[0]
    else:
        return "Tamil" # Default to Tamil if unsure, or change to "Other"

def clean_movie_name(title):
    # Extracts text before the year (e.g., "Movie Name (2024)..." -> "Movie Name")
    match = re.search(r"^(.*?)\s*\(\d{4}\)", title)
    if match:
        return match.group(1).strip()
    return title.split(" - ")[0].strip() # Fallback if no year found

def scrape_movies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use a mobile user agent to potentially get simpler pages, or standard desktop
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        print(f"Accessing {TARGET_URL}...")
        try:
            page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"Error loading homepage: {e}")
            browser.close()
            return
        
        # Get thread links
        link_elements = page.locator('a[href*="/index.php?/forums/topic/"]').all()
        
        # Deduplicate links while keeping order
        thread_urls = []
        seen_urls = set()
        for link in link_elements:
            try:
                href = link.get_attribute("href")
                if href and href not in seen_urls:
                    thread_urls.append(href)
                    seen_urls.add(href)
            except:
                continue

        print(f"Found {len(thread_urls)} threads. Checking top 10...")
        
        new_entries = []

        # Check top 10 latest threads
        for url in thread_urls[:10]:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # 1. Extract Title
                title_element = page.locator("h1").first
                if title_element.count() == 0: continue
                raw_title = title_element.inner_text().strip()
                
                # 2. Process Group and Name
                group = get_language_group(raw_title)
                name = clean_movie_name(raw_title)
                
                # 3. Extract Poster Image
                # Looks for the first image in the main post content area
                image_url = ""
                # Try generic selectors for forum post images
                img_locator = page.locator("div[data-role='commentContent'] img").first
                if img_locator.count() > 0:
                    image_url = img_locator.get_attribute("src")
                
                # 4. Extract Magnet Link
                magnet_link = ""
                magnet_element = page.locator('a[href^="magnet:?"]').first
                if magnet_element.count() > 0:
                    magnet_link = magnet_element.get_attribute("href")
                
                # Only add if we found a magnet
                if magnet_link:
                    # Format: Group | Name | Image | Magnet
                    entry = f"{group} | {name} | {image_url} | {magnet_link}"
                    new_entries.append(entry)
                    print(f"  -> Found: {name} ({group})")
                    
            except Exception as e:
                print(f"  -> Error scraping page: {e}")
                continue

        browser.close()
        update_output_file(new_entries)

def update_output_file(new_entries):
    if not os.path.exists(OUTPUT_FILE):
        open(OUTPUT_FILE, 'w').close()
        
    # Read existing file to check for duplicate MAGNET LINKS (the unique ID)
    with open(OUTPUT_FILE, 'r') as f:
        existing_lines = f.readlines()
    
    # Extract just the magnet links from the file to check against
    existing_magnets = set()
    for line in existing_lines:
        parts = line.split("|")
        if len(parts) >= 4:
            existing_magnets.add(parts[-1].strip())
    
    with open(OUTPUT_FILE, 'a') as f:
        count = 0
        for entry in new_entries:
            # Check if the magnet link (last part of the new entry) is already known
            new_magnet = entry.split("|")[-1].strip()
            if new_magnet not in existing_magnets:
                f.write(entry + "\n")
                count += 1
                existing_magnets.add(new_magnet) # Prevent dupes within same run
        print(f"Added {count} new movies to {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape_movies()
