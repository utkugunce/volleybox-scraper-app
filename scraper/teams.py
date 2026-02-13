"""
Team/Club scraping module for women.volleybox.net
Handles team list and individual team profile scraping.
"""

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
    Scrape a single team/club profile page.

    Args:
        scraper: VolleyboxScraper instance
        url: Team profile URL

    Returns:
        Dict with detailed team info
    """
    console.print(f"[bold cyan]🏐 Takım profili çekiliyor: {url}[/bold cyan]")

    soup = scraper.get_page(url)
    if not soup:
        return None

    team = {"url": url}

    # --- Name ---
    name_el = soup.select_one("h1, .team-name, .club-name, .profile-name")
    if name_el:
        team["name"] = name_el.get_text(strip=True)

    # --- Info section ---
    info_section = soup.select_one(".club-info, .team-info, .info-table, .details, main")
    if not info_section:
        info_section = soup

    field_map = {
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

    # Table rows
    for row in info_section.select("tr"):
        cells = row.select("td, th")
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True).lower()
            value = cells[1].get_text(strip=True)
            for tr_key, en_key in field_map.items():
                if tr_key in label:
                    team[en_key] = value
                    break

    # Definition lists
    dts = info_section.select("dt")
    dds = info_section.select("dd")
    for dt, dd in zip(dts, dds):
        label = dt.get_text(strip=True).lower()
        value = dd.get_text(strip=True)
        for tr_key, en_key in field_map.items():
            if tr_key in label:
                team[en_key] = value
                break

    # --- Current Roster ---
    roster = []
    
    # Heuristic: Find the container with the most player links
    candidates = []
    # Look for any div or section that might contain players
    for container in soup.select("div, section, table"):
        links = container.select("a[href*='-p']")
        # Filter out links that are too deep (don't count children's links if parent already counted? 
        # Actually selecting all is fine, we just want the dense one)
        
        # We need a container that has direct-ish access.
        # Let's just look at all player links and find their common ancestor?
        pass

    # Better approach: Get all player links, find the most common parent (limit to relevant block elements)
    all_player_links = soup.select("a[href*='-p']")
    if all_player_links:
        from collections import Counter
        parents = []
        for link in all_player_links:
            # Find the closest semantic parent (div, ul, table, section)
            p = link.find_parent(["div", "ul", "table", "section", "tbody"])
            if p:
                parents.append(p)
        
        if parents:
            # Find the parent that appears most often (this is likely the roster container)
            most_common_parent = Counter(parents).most_common(1)[0][0]
            
            # Now extract distinct players from this container
            seen_urls = set()
            for player_el in most_common_parent.select("a[href*='-p']"):
                player_href = player_el.get("href", "")
                if re.search(r'-p\d+$', player_href):
                    full_url = player_href if player_href.startswith("http") else f"https://women.volleybox.net{player_href}"
                    
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)
                    
                    player_name = player_el.get_text(strip=True)
                    # Fallback for name
                    if not player_name:
                        player_name = player_el.get("title", "").strip()
                    if not player_name:
                        img = player_el.select_one("img")
                        if img:
                            player_name = img.get("alt", "").strip() or img.get("title", "").strip()
                            
                    if player_name and len(player_name) > 1:
                        # Try to find position, number, etc.
                        # Usually position is in a sibling or close by
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
