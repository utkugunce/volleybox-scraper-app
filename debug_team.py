"""Debug script to save team page HTML."""
from scraper.core import VolleyboxScraper

scraper = VolleyboxScraper()
# VakifBank URL
url = "https://women.volleybox.net/tr/vakfbank-t2309"
soup = scraper.get_page(url)

if soup:
    with open("team_vakif.html", "w", encoding="utf-8") as f:
        f.write(str(soup))
    print("Saved HTML to team_vakif.html")
else:
    print("Failed to load page")

scraper.close()
