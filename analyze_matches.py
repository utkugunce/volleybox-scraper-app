"""Analyze match page HTML to find match selector."""
from bs4 import BeautifulSoup
import re

with open("tournament_matches.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")

print(f"HTML len: {len(html)}")

# Find match scores as anchors
scores = soup.select(".score, .result, .match-score")
print(f"Total scores found: {len(scores)}")

if scores:
    # Analyze parent of scores
    for i, score in enumerate(scores[:3]):
        print(f"\nScore {i}: {score.get_text(strip=True)}")
        parents = []
        p = score.parent
        while p and p.name != "body":
            cls = ".".join(p.get("class", []))
            parents.append(f"{p.name}{'.' if cls else ''}{cls}")
            if len(parents) > 5: break
            p = p.parent
        print(f"  Path: {' > '.join(parents)}")

# Find team links in close proximity
team_links = soup.select("a[href*='-t']")
print(f"Total team links: {len(team_links)}")

# Heuristic: Match row usually has 2 team links and 1 score
match_rows = []
for row in soup.select("tr, .match, .game, div[class*='match']"):
    teams = row.select("a[href*='-t']")
    if len(teams) >= 2:
        score_el = row.select_one(".score, .result, span[class*='score']")
        if score_el:
            match_rows.append(row)

print(f"Heuristic match rows found: {len(match_rows)}")
if match_rows:
    sample = match_rows[0]
    print(f"\nSample match row HTML snippet:\n{str(sample)[:200]}...")
