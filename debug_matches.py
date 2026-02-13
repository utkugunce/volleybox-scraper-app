"""Debug script to save tournament matches page HTML."""
from scraper.core import VolleyboxScraper

scraper = VolleyboxScraper()
url = "https://women.volleybox.net/women-turkiye-kadnlar-voleybol-2-ligi-2025-26-o38677/matches"
soup = scraper.get_page(url)

if soup:
    with open("tournament_matches.html", "w", encoding="utf-8") as f:
        f.write(str(soup))
    print("Saved HTML to tournament_matches.html")
else:
    print("Failed to load page")

scraper.close()
