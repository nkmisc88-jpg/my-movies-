import os
import re
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
TARGET_URL = "https://www.1tamilmv.earth/"
OUTPUT_FILE = "movies.txt"
# ---------------------

def get_language_group(title):
    t_lower = title.lower()
    if "multi" in t_lower or ("tam" in t_lower and "tel" in t_lower):
        return "Multi"
    elif "tamil" in t_lower: return "Tamil"
    elif "telugu" in t_lower: return "Telugu"
    elif "hindi" in t_lower: return "Hindi"
    elif "malayalam" in t_lower: return "Malayalam"
    elif "kannada" in t_lower: return "Kannada"
    elif "english" in t_lower: return "English"
    return "Tamil"

def clean_movie_name(title):
    # Extracts text before the year (e.g. "Movie Name (2024)...")
    match = re.search(r"^(.*?)\s*\(\d{4}\)", title)
    if match: return match.group(1).strip()
    return title.split("-")[0].strip()

def scrape_movies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use a real Chrome User-Agent to avoid blocks
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()
        
        print(f"Accessing {TARGET_URL}...")
        try:
            page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"Error loading homepage: {e}")
            browser.close(); return

        # FIX: The command is .all(), NOT .all_links()
        # We grab all links that look like a forum topic
        all_link_elements = page.locator('a[href*="topic"]').all()
        
        thread_urls = []
        seen = set()
        
        # Extract hrefs safely
        for link in all_link_elements:
            try:
                href = link.get_attribute("href")
                if href and "/topic/" in href and href not in seen:
                    thread_urls.append(href)
                    seen.add(href)
            except: continue

        print(f"Found {len(thread_urls)} movie threads. Checking Top 20...")
        
        new_entries = []
        
        # INCREASED LIMIT: Check top 20 to catch movies further down the list
        for url in thread_urls[:20]:
            try:
                print(f"Checking: {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # 1. Get Title
                title_el = page.locator("h1").first
                if title_el.count() == 0: continue
                raw_title = title_el.inner_text().strip()
                
                # 2. Get Magnet
                magnet_el = page.locator('a[href^="magnet:?"]').first
                if magnet_el.count() > 0:
                    magnet_link = magnet_el.get_attribute("href")
                    
                    # 3. Get Image
                    image_url = "No Image"
                    post_content = page.locator('div[data-role="commentContent"]').first
                    if post_content.count() > 0:
                        img = post_content.locator("img").first
                        if img.count() > 0: image_url = img.get_attribute("src")

                    # 4. Format Data
                    group = get_language_group(raw_title)
                    name = clean_movie_name(raw_title)
                    
                    entry = f"{group} | {name} | {image_url} | {magnet_link}"
                    new_entries.append(entry)
                    print(f"  -> Found: {name}")
                    
            except Exception as e:
                print(f"  -> Skipped due to error: {e}")
                continue

        browser.close()
        update_output_file(new_entries)

def update_output_file(new_entries):
    # Read existing file to avoid duplicates
    existing_magnets = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r') as f:
            for line in f:
                parts = line.split("|")
                if len(parts) >= 4:
                    existing_magnets.add(parts[-1].strip())

    count = 0
    with open(OUTPUT_FILE, 'a') as f:
        for entry in new_entries:
            magnet = entry.split("|")[-1].strip()
            # Only add if magnet is NOT in file
            if magnet not in existing_magnets:
                f.write(entry + "\n")
                count += 1
    
    print(f"Successfully added {count} new movies.")

if __name__ == "__main__":
    scrape_movies()
