"""Debug script to examine homepage HTML structure for transfer data.
Waits longer for dynamic content to load."""
import re
import time
from scraper.core import VolleyboxScraper

scraper = VolleyboxScraper()
page = scraper._get_page()

# Navigate to homepage
page.get("https://women.volleybox.net/tr/")
time.sleep(3)

# Wait for Cloudflare
print("Waiting for Cloudflare...")
for i in range(30):
    title = page.title.lower() if page.title else ""
    if "just a moment" not in title:
        html = page.html or ""
        if len(html) > 2000:
            print(f"Cloudflare passed after {i*2}s")
            break
    time.sleep(2)

# Now wait for dynamic content to load
print("Waiting for dynamic content...")
time.sleep(8)

html = page.html
print(f"HTML length: {len(html)}")

# Check for player links
player_count = len(re.findall(r'-p\d+', html))
team_count = len(re.findall(r'-t\d+', html))
print(f"Player link patterns: {player_count}")
print(f"Team link patterns: {team_count}")

# Save a portion of the HTML for analysis
with open("debug_html_output.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Saved full HTML to debug_html_output.html")

# Look for transfer-related sections
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, "lxml")

# Print first few links
all_links = soup.select("a[href]")
print(f"\nTotal links on page: {len(all_links)}")

# Print links that contain player-like patterns
p_links = [a for a in all_links if re.search(r'-p\d+', a.get("href", ""))]
print(f"Player links: {len(p_links)}")
for pl in p_links[:10]:
    print(f"  {pl.get_text(strip=True)[:50]} -> {pl.get('href', '')[:80]}")

# Print links that contain team patterns
t_links = [a for a in all_links if re.search(r'-t\d+', a.get("href", ""))]
print(f"\nTeam links: {len(t_links)}")
for tl in t_links[:10]:
    print(f"  {tl.get_text(strip=True)[:50]} -> {tl.get('href', '')[:80]}")

# Look for transfer keyword
transfer_mentions = html.lower().count("transfer")
print(f"\n'transfer' mentions in HTML: {transfer_mentions}")

scraper.close()
