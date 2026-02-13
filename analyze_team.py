"""Analyze team page HTML to find roster selector."""
from bs4 import BeautifulSoup
import re

with open("team_vakif.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")

print(f"HTML len: {len(html)}")

# Find player links
player_links = soup.select("a[href*='-p']")
print(f"Total player links found: {len(player_links)}")

if not player_links:
    print("No player links found!")
else:
    # Get parents of first few links
    for i, link in enumerate(player_links[:3]):
        print(f"\nLink {i}: {link.get_text(strip=True)}")
        parents = []
        p = link.parent
        while p and p.name != "body":
            cls = ".".join(p.get("class", []))
            parents.append(f"{p.name}{'.' if cls else ''}{cls}")
            if len(parents) > 5: break
            p = p.parent
        print(f"  Path: {' > '.join(parents)}")

# Search for keywords
for kw in ["Roster", "Squad", "Players", "Kadro", "Oyuncular"]:
    found = soup.find(string=re.compile(kw, re.I))
    if found:
        parent = found.parent
        print(f"\nKeyword '{kw}' found in <{parent.name} class='{parent.get('class')}'>")
