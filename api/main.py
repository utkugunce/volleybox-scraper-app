from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import sys
import os
from contextlib import asynccontextmanager

# Add parent directory to path so we can import scraper
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.core import VolleyboxScraper
from scraper.teams import scrape_team_list, scrape_team_profile
from scraper.players import scrape_player_list, scrape_player_profile
from scraper.tournaments import scrape_tournament_list, scrape_tournament_detail
from scraper.transfers import scrape_transfers

# Global scraper instance
scraper: Optional[VolleyboxScraper] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global scraper
    print("Starting scraper...")
    scraper = VolleyboxScraper(headless=False) # Keep headful for cloudflare
    yield
    print("Closing scraper...")
    if scraper:
        scraper.close()

app = FastAPI(title="Volleybox API", lifespan=lifespan)

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Volleybox API is running"}

@app.get("/teams")
def get_teams(page: int = 1, limit: int = 0):
    """List teams with optional pagination limit."""
    # Note: scraping multiple pages takes time.
    # For now, let's just scrape the requested page count if limit is high, 
    # but the scraper function scrape_team_list takes page_limit.
    # Let's map 'limit' loosely to 'page_limit' for now or just scrape 1 page.
    
    # Actually, scrape_team_list's page_limit means "scrape X pages".
    # Let's default to 1 page for speed in API.
    data = scrape_team_list(scraper, page_limit=1)
    return data

@app.get("/teams/detail")
def get_team_detail(url: str):
    """Get detailed team info."""
    data = scrape_team_profile(scraper, url)
    if not data:
        raise HTTPException(status_code=404, detail="Team not found or scrape failed")
    return data

@app.get("/players")
def get_players(page: int = 1):
    """List players."""
    data = scrape_player_list(scraper, page_limit=1)
    return data

@app.get("/players/detail")
def get_player_detail(url: str):
    """Get detailed player info."""
    data = scrape_player_profile(scraper, url)
    if not data:
        raise HTTPException(status_code=404, detail="Player not found")
    return data

@app.get("/tournaments")
def get_tournaments():
    """List tournaments."""
    data = scrape_tournament_list(scraper, page_limit=1)
    return data

@app.get("/tournaments/detail")
def get_tournament_detail(url: str):
    """Get tournament detail."""
    data = scrape_tournament_detail(scraper, url)
    if not data:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return data

@app.get("/search")
def search(q: str):
    """Search functionality."""
    # We need to implement search_site logic here or import it
    # Since search_site was in main.py, let's duplicate the logic or refactor.
    # For speed, I'll reimplement specific search logic here or move search_site to a common module.
    # Let's try to import it if possible, but main.py has argparse logic.
    # Better to copy the logic or refactor. I'll copy the core logic for now.
    
    url = f"https://women.volleybox.net/{scraper.lang}/search"
    soup = scraper.get_page(url, params={"q": q})
    
    if not soup:
        return []

    results = []
    for link in soup.select("a"):
        href = link.get("href", "")
        text = link.get_text(strip=True)
        
        if not text or len(text) < 2:
            continue
            
        import re
        result_type = None
        if re.search(r'-p\d+$', href):
            result_type = "player"
        elif re.search(r'-t\d+$', href):
            result_type = "team"
        elif re.search(r'-c\d+$', href):
            result_type = "tournament"
        else:
            continue
            
        full_url = href if href.startswith("http") else f"https://women.volleybox.net{href}"
        results.append({
            "name": text,
            "type": result_type,
            "url": full_url,
        })
        
    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)
            
    return unique
