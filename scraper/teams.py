"""
Team/Club scraping module for women.volleybox.net
Handles team list and individual team profile scraping.
"""

import time
import re
from rich.console import Console
from rich.progress import track

console = Console()


def scrape_team_list(scraper, page_limit=5):
    """
    Scrape the team/club list.

    Args:
        scraper: VolleyboxScraper instance
        page_limit: Max number of pages to scrape (0 = all)

    Returns:
        List of dicts with team summary info
    """
    teams = []
    page = 1

    console.print("[bold cyan]📋 Takım listesi çekiliyor...[/bold cyan]")

    while True:
        if page_limit and page > page_limit:
            break

        url = scraper.build_url("clubs")
        params = {"page": page} if page > 1 else None
        soup = scraper.get_page(url, params=params)

        if not soup:
            console.print(f"  [red]Sayfa {page} çekilemedi, durduruluyor.[/red]")
            break

        # Find team entries
        team_items = soup.select("a[href*='-t']")

        if not team_items:
            team_items = soup.select(".club-item, .team-card, .team-row, .list-item a[href*='/t']")

        if not team_items:
            console.print(f"  [dim]Sayfa {page}: Takım bulunamadı, durduruluyor.[/dim]")
            break

        page_count = 0
        seen_urls = {t.get("url", "") for t in teams}

        for item in team_items:
            href = item.get("href", "")
            # Match team URLs like /tr/name-t12345
            if not re.search(r'-t\d+$', href):
                continue

            full_url = href if href.startswith("http") else f"https://women.volleybox.net{href}"

            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            name = item.get_text(strip=True)
            if not name or len(name) < 2:
                continue

            # Try to find additional info
            parent = item.parent
            country = ""
            league = ""

            if parent:
                sibling_text = parent.get_text(separator="|", strip=True)
                parts = sibling_text.split("|")
                for part in parts:
                    part = part.strip()
                    if part != name and len(part) > 1:
                        if not country:
                            country = part
                        elif not league:
                            league = part

            # Try to get team logo
            logo_url = ""
            logo_img = item.select_one("img")
            if not logo_img and parent:
                logo_img = parent.select_one("img")
            if logo_img:
                src = logo_img.get("src", "")
                if src:
                    logo_url = src if src.startswith("http") else f"https://women.volleybox.net{src}"

            team_data = {
                "name": name,
                "url": full_url,
                "country": country,
                "league": league,
                "logo_url": logo_url,
            }
            teams.append(team_data)
            page_count += 1

        console.print(f"  [green]Sayfa {page}: {page_count} takım bulundu[/green]")

        # Check for next page
        next_link = soup.select_one("a[rel='next'], .pagination .next a, a.next-page")
        if not next_link:
            pagination_links = soup.select(".pagination a, nav a")
            has_next = False
            for plink in pagination_links:
                text = plink.get_text(strip=True)
                if text.isdigit() and int(text) > page:
                    has_next = True
                    break
                if "›" in text or "»" in text:
                    has_next = True
                    break
            if not has_next:
                break

        page += 1

    console.print(f"[bold green]✓ Toplam {len(teams)} takım bulundu[/bold green]")
    return teams


def scrape_team_profile(scraper, url):
    """
    Scrape a single team/club profile page using DrissionPage directly.

    Args:
        scraper: VolleyboxScraper instance
        url: Team profile URL

    Returns:
        Dict with detailed team info
    """
    console.print(f"[bold cyan]🏐 Takım profili çekiliyor: {url}[/bold cyan]")

    page = scraper._get_page()
    page.get(url)

    if not scraper._wait_for_cloudflare():
        console.print("[red]Cloudflare geçilemedi.[/red]")
        return None
    
    time.sleep(1)
    team = {"url": url}

    # --- Name ---
    try:
        name_el = page.ele('t:h1')
        if name_el:
            team["name"] = name_el.text.strip()
            console.print(f"  Takım adı: {team['name']}")
    except Exception:
        team["name"] = "N/A"

    # --- Info section (dl/dt/dd structure) ---
    # Volleybox info is often in a dl inside a div.display-flex
    # key is in dt, value in dd (or just text after dt if no dd?)
    # Based on trace: dt.info-header -> parent div.display-flex -> parent dl
    
    info_map = {
        "ülke": "country",
        "country": "country",
        "şehir": "city",
        "city": "city",
        "kuruluş": "founded",
        "founded": "founded",
        "salon": "arena",
        "arena": "arena",
        "hall": "arena",
        "antrenör": "coach",
        "coach": "coach",
        "başkan": "president",
        "president": "president",
    }

    try:
        # Find all dt elements which are labels
        dts = page.eles('t:dt')
        for dt in dts:
            label = dt.text.strip().lower().replace(":", "")
            
            # The value is usually in the sibling or next element
            # Structure is often dt... dd... or dt... span...
            # In the trace it showed dt is inside a div.display-flex. 
            # The value might be a sibling element or text node.
            
            val_el = dt.next()
            if val_el:
                value = val_el.text.strip()
                
                for k, v in info_map.items():
                    if k in label:
                        team[v] = value
                        # print(f"    {v}: {value}")
                        break
    except Exception as e:
        console.print(f"  [yellow]Bilgi çekme hatası: {e}[/yellow]")

    # --- Roster (div.team-roster-row) ---
    roster = []
                        position = ""
                        number = ""
                        
                        # Check previous sibling for number
                        # Check parent text for position
                        
                        roster.append({
                            "name": player_name,
                            "url": full_url,
                            "position": position,
                            "number": number,
                        })

    if roster:
        team["roster"] = roster

    # --- Trophies/Achievements ---
    trophies = []
    trophy_section = soup.select_one(".trophies, .achievements, .awards")
    if trophy_section:
        for item in trophy_section.select("li, .trophy-item, tr"):
            text = item.get_text(strip=True)
            if text:
                trophies.append(text)

    if trophies:
        team["trophies"] = trophies

    # --- Logo ---
    logo = soup.select_one(".team-logo img, .club-logo img, .logo img")
    if logo:
        src = logo.get("src", "")
        if src:
            team["logo_url"] = src if src.startswith("http") else f"https://women.volleybox.net{src}"

    console.print(f"[bold green]✓ Profil çekildi: {team.get('name', 'N/A')}[/bold green]")
    return team


def scrape_teams_detail(scraper, team_list, limit=0):
    """
    Scrape detailed profiles for a list of teams.

    Args:
        scraper: VolleyboxScraper instance
        team_list: List of dicts with 'url' key
        limit: Max teams to scrape (0 = all)

    Returns:
        List of detailed team dicts
    """
    if limit:
        team_list = team_list[:limit]

    detailed = []
    for team_summary in track(team_list, description="Takım detayları çekiliyor..."):
        profile = scrape_team_profile(scraper, team_summary["url"])
        if profile:
            merged = {**team_summary, **profile}
            detailed.append(merged)

    return detailed
