"""
Player scraping module for women.volleybox.net
Handles player list and individual player profile scraping.
"""

import re
from rich.console import Console
from rich.progress import track

console = Console()


def scrape_player_list(scraper, page_limit=5):
    """
    Scrape the player list with pagination.

    Args:
        scraper: VolleyboxScraper instance
        page_limit: Max number of pages to scrape (0 = all)

    Returns:
        List of dicts with player summary info
    """
    players = []
    page = 1

    console.print("[bold cyan]📋 Oyuncu listesi çekiliyor...[/bold cyan]")

    while True:
        if page_limit and page > page_limit:
            break

        url = scraper.build_url("players")
        params = {"page": page} if page > 1 else None
        soup = scraper.get_page(url, params=params)

        if not soup:
            console.print(f"  [red]Sayfa {page} çekilemedi, durduruluyor.[/red]")
            break

        # Find player entries — volleybox uses various list/card layouts
        player_items = soup.select("a[href*='-p']")

        if not player_items:
            # Try alternate selectors
            player_items = soup.select(".player-item, .player-card, .player-row, .list-item a[href*='/p']")

        if not player_items:
            console.print(f"  [dim]Sayfa {page}: Oyuncu bulunamadı, durduruluyor.[/dim]")
            break

        page_count = 0
        seen_urls = {p.get("url", "") for p in players}

        for item in player_items:
            href = item.get("href", "")
            # Match player URLs like /tr/name-p12345
            if not re.search(r'-p\d+$', href):
                continue

            full_url = href if href.startswith("http") else f"https://women.volleybox.net{href}"

            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            name = item.get_text(strip=True)
            if not name or len(name) < 2:
                continue

            # Try to find additional info from surrounding elements
            parent = item.parent
            position = ""
            nationality = ""

            if parent:
                # Look for position/nationality text near the player link
                sibling_text = parent.get_text(separator="|", strip=True)
                parts = sibling_text.split("|")
                for part in parts:
                    part = part.strip()
                    if part != name and len(part) > 1:
                        if not position:
                            position = part
                        elif not nationality:
                            nationality = part

            player_data = {
                "name": name,
                "url": full_url,
                "position": position,
                "nationality": nationality,
            }
            players.append(player_data)
            page_count += 1

        console.print(f"  [green]Sayfa {page}: {page_count} oyuncu bulundu[/green]")

        # Check for next page
        next_link = soup.select_one("a[rel='next'], .pagination .next a, a.next-page")
        if not next_link:
            # Also check if there's a pagination with higher page numbers
            pagination_links = soup.select(".pagination a, nav a")
            has_next = False
            for plink in pagination_links:
                href = plink.get("href", "")
                text = plink.get_text(strip=True)
                if text.isdigit() and int(text) > page:
                    has_next = True
                    break
                if "next" in href.lower() or "›" in text or "»" in text:
                    has_next = True
                    break
            if not has_next:
                break

        page += 1

    console.print(f"[bold green]✓ Toplam {len(players)} oyuncu bulundu[/bold green]")
    return players


def scrape_player_profile(scraper, url):
    """
    Scrape a single player's profile page.

    Args:
        scraper: VolleyboxScraper instance
        url: Player profile URL

    Returns:
        Dict with detailed player info
    """
    console.print(f"[bold cyan]👤 Oyuncu profili çekiliyor: {url}[/bold cyan]")

    soup = scraper.get_page(url)
    if not soup:
        return None

    player = {"url": url}

    # --- Name ---
    name_el = soup.select_one("h1, .player-name, .profile-name, .name")
    if name_el:
        player["name"] = name_el.get_text(strip=True)

    # --- Profile info table/section ---
    # Look for key-value pairs in the profile
    info_section = soup.select_one(".profile-info, .player-info, .info-table, .details, main")
    if not info_section:
        info_section = soup

    # Common field mappings (Turkish labels → keys)
    field_map = {
        "pozisyon": "position",
        "position": "position",
        "doğum tarihi": "birth_date",
        "date of birth": "birth_date",
        "birthday": "birth_date",
        "boy": "height",
        "height": "height",
        "kilo": "weight",
        "weight": "weight",
        "uyruk": "nationality",
        "nationality": "nationality",
        "ülke": "nationality",
        "country": "nationality",
        "takım": "current_team",
        "team": "current_team",
        "kulüp": "current_team",
        "club": "current_team",
        "smaç": "spike_height",
        "spike": "spike_height",
        "blok": "block_height",
        "block": "block_height",
    }

    # Try to find info rows (dt/dd, th/td, label/value pairs)
    # Pattern 1: Table rows
    for row in info_section.select("tr"):
        cells = row.select("td, th")
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True).lower()
            value = cells[1].get_text(strip=True)
            for tr_key, en_key in field_map.items():
                if tr_key in label:
                    player[en_key] = value
                    break

    # Pattern 2: Definition lists
    dts = info_section.select("dt")
    dds = info_section.select("dd")
    for dt, dd in zip(dts, dds):
        label = dt.get_text(strip=True).lower()
        value = dd.get_text(strip=True)
        for tr_key, en_key in field_map.items():
            if tr_key in label:
                player[en_key] = value
                break

    # Pattern 3: Generic label-value divs
    for div in info_section.select("div"):
        text = div.get_text(separator="|", strip=True)
        parts = text.split("|")
        if len(parts) == 2:
            label = parts[0].strip().lower()
            value = parts[1].strip()
            for tr_key, en_key in field_map.items():
                if tr_key in label:
                    player[en_key] = value
                    break

    # --- Career / Transfer history ---
    career = []
    career_section = soup.select_one(".career, .transfer-history, .history, .teams-history")
    if career_section:
        for row in career_section.select("tr, .career-item, .history-item"):
            cells = row.select("td, span, div")
            if len(cells) >= 2:
                season = cells[0].get_text(strip=True)
                team = cells[1].get_text(strip=True)
                career_entry = {"season": season, "team": team}
                if len(cells) >= 3:
                    career_entry["league"] = cells[2].get_text(strip=True)
                career.append(career_entry)

    if career:
        player["career"] = career

    # --- Photo URL ---
    img = soup.select_one(".player-photo img, .profile-photo img, .photo img, img.player-img")
    if img:
        src = img.get("src", "")
        if src:
            player["photo_url"] = src if src.startswith("http") else f"https://women.volleybox.net{src}"

    console.print(f"[bold green]✓ Profil çekildi: {player.get('name', 'N/A')}[/bold green]")
    return player


def scrape_players_detail(scraper, player_list, limit=0):
    """
    Scrape detailed profiles for a list of players.

    Args:
        scraper: VolleyboxScraper instance
        player_list: List of dicts with 'url' key
        limit: Max players to scrape (0 = all)

    Returns:
        List of detailed player dicts
    """
    if limit:
        player_list = player_list[:limit]

    detailed = []
    for player_summary in track(player_list, description="Oyuncu detayları çekiliyor..."):
        profile = scrape_player_profile(scraper, player_summary["url"])
        if profile:
            # Merge summary info with detailed info
            merged = {**player_summary, **profile}
            detailed.append(merged)

    return detailed
