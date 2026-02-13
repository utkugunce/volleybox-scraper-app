"""
Tournament/League scraping module for women.volleybox.net
Handles tournament listings and detailed tournament data.
"""

import re
import time
from rich.console import Console
from rich.progress import track

console = Console()


def scrape_tournament_list(scraper, page_limit=5):
    """
    Scrape the tournament/league list.

    Args:
        scraper: VolleyboxScraper instance
        page_limit: Max number of pages to scrape (0 = all)

    Returns:
        List of dicts with tournament summary info
    """
    tournaments = []
    page = 1

    console.print("[bold cyan]📋 Turnuva listesi çekiliyor...[/bold cyan]")

    while True:
        if page_limit and page > page_limit:
            break

        url = scraper.build_url("clubs-tournaments")
        params = {"page": page} if page > 1 else None
        soup = scraper.get_page(url, params=params)

        if not soup:
            console.print(f"  [red]Sayfa {page} çekilemedi, durduruluyor.[/red]")
            break

        # Find tournament entries
        tournament_items = soup.select("a[href*='-c']")

        if not tournament_items:
            tournament_items = soup.select(".tournament-item, .league-card, .competition-row")

        if not tournament_items:
            console.print(f"  [dim]Sayfa {page}: Turnuva bulunamadı, durduruluyor.[/dim]")
            break

        page_count = 0
        seen_urls = {t.get("url", "") for t in tournaments}

        for item in tournament_items:
            href = item.get("href", "")
            # Match tournament URLs like /tr/name-c12345
            if not re.search(r'-c\d+$', href):
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
            season = ""

            if parent:
                sibling_text = parent.get_text(separator="|", strip=True)
                parts = sibling_text.split("|")
                for part in parts:
                    part = part.strip()
                    if part != name and len(part) > 1:
                        # Check if it looks like a season (e.g., 2024/25)
                        if re.match(r'\d{4}', part):
                            season = part
                        elif not country:
                            country = part

            tournament_data = {
                "name": name,
                "url": full_url,
                "country": country,
                "season": season,
            }
            tournaments.append(tournament_data)
            page_count += 1

        console.print(f"  [green]Sayfa {page}: {page_count} turnuva bulundu[/green]")

        # Check for next page
        next_link = soup.select_one("a[rel='next'], .pagination .next a")
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

    console.print(f"[bold green]✓ Toplam {len(tournaments)} turnuva bulundu[/bold green]")
    return tournaments


def scrape_tournament_detail(scraper, url):
    """
    Scrape a single tournament/league detail page.

    Args:
        scraper: VolleyboxScraper instance
        url: Tournament URL

    Returns:
        Dict with detailed tournament info
    """
    console.print(f"[bold cyan]🏆 Turnuva detayı çekiliyor: {url}[/bold cyan]")

    soup = scraper.get_page(url)
    if not soup:
        return None

    tournament = {"url": url}

    # --- Name ---
    name_el = soup.select_one("h1, .tournament-name, .league-name, .competition-name")
    if name_el:
        tournament["name"] = name_el.get_text(strip=True)

    # --- Info section ---
    info_section = soup.select_one(".tournament-info, .league-info, .competition-info, .details, main")
    if not info_section:
        info_section = soup

    field_map = {
        "ülke": "country",
        "country": "country",
        "sezon": "season",
        "season": "season",
        "başlangıç": "start_date",
        "start": "start_date",
        "bitiş": "end_date",
        "end": "end_date",
        "takım sayısı": "team_count",
        "teams": "team_count",
    }

    for row in info_section.select("tr"):
        cells = row.select("td, th")
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True).lower()
            value = cells[1].get_text(strip=True)
            for tr_key, en_key in field_map.items():
                if tr_key in label:
                    tournament[en_key] = value
                    break

    # --- Standings/Table ---
    standings = []
    table = soup.select_one(".standings, .ranking-table, .league-table, table.table")
    if table:
        headers = [th.get_text(strip=True) for th in table.select("thead th, tr:first-child th")]
        for row in table.select("tbody tr, tr")[1:]:  # Skip header row
            cells = row.select("td")
            if not cells:
                continue

            row_data = {}
            if headers:
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        row_data[headers[i]] = cell.get_text(strip=True)
                    else:
                        row_data[f"col_{i}"] = cell.get_text(strip=True)
            else:
                for i, cell in enumerate(cells):
                    row_data[f"col_{i}"] = cell.get_text(strip=True)

            # Try to find team link
            team_link = row.select_one("a[href*='-t']")
            if team_link:
                row_data["team_name"] = team_link.get_text(strip=True)
                href = team_link.get("href", "")
                row_data["team_url"] = href if href.startswith("http") else f"https://women.volleybox.net{href}"

            if row_data:
                standings.append(row_data)

    if standings:
        tournament["standings"] = standings

    # --- Teams list ---
    teams = []
    for team_link in soup.select("a[href*='-t']"):
        href = team_link.get("href", "")
        if re.search(r'-t\d+$', href):
            name = team_link.get_text(strip=True)
            team_url = href if href.startswith("http") else f"https://women.volleybox.net{href}"
            if name and len(name) > 1:
                teams.append({"name": name, "url": team_url})

    # Deduplicate
    seen = set()
    unique_teams = []
    for t in teams:
        if t["url"] not in seen:
            seen.add(t["url"])
            unique_teams.append(t)
    teams = unique_teams

    if teams:
        tournament["teams"] = teams

    # --- Match results ---
    matches = []
    match_section = soup.select_one(".matches, .results, .schedule, .fixtures")
    if match_section:
        for match_el in match_section.select(".match, .match-row, tr"):
            match_data = {}
            teams_in_match = match_el.select("a[href*='-t']")
            if len(teams_in_match) >= 2:
                match_data["home_team"] = teams_in_match[0].get_text(strip=True)
                match_data["away_team"] = teams_in_match[1].get_text(strip=True)

            score_el = match_el.select_one(".score, .result")
            if score_el:
                match_data["score"] = score_el.get_text(strip=True)

            date_el = match_el.select_one(".date, .match-date, time")
            if date_el:
                match_data["date"] = date_el.get_text(strip=True)

            if match_data:
                matches.append(match_data)

    if matches:
        tournament["matches"] = matches

    console.print(f"[bold green]✓ Turnuva çekildi: {tournament.get('name', 'N/A')}[/bold green]")
    return tournament


def scrape_tournament_matches(scraper, url):
    """
    Scrape all matches from a tournament matches page.
    Handles multiple rounds and 'Show More' pagination using browser interaction.

    Args:
        scraper: VolleyboxScraper instance
        url: Tournament matches URL

    Returns:
        List of dicts with match data
    """
    console.print(f"[bold cyan]🏐 Turnuva maçları çekiliyor: {url}[/bold cyan]")

    page = scraper._get_page()
    page.get(url)

    # Initial Cloudflare check
    if not scraper._wait_for_cloudflare():
        console.print("[red]Cloudflare geçilemedi, maçlar çekilemiyor.[/red]")
        return []

    # Get tournament name
    tournament_name = "N/A"
    name_el = page.ele('t:h1')
    if name_el:
        tournament_name = name_el.text

    all_matches = []
    seen_match_ids = set()

    # Find round buttons with a more robust selector (onclick contains changeTournamentRound)
    try:
        page.wait.ele_displayed('xpath://button[contains(@onclick, "changeTournamentRound")]', timeout=15)
        # Wait a bit more for all buttons to render in the horizontal scroll
        time.sleep(2)
    except Exception:
        pass

    round_selector = 'xpath://button[contains(@onclick, "changeTournamentRound")]'
    round_buttons = page.eles(round_selector)
    if not round_buttons:
        # Fallback to the class if XPath fails
        round_buttons = page.eles('.transfer-league-btn:not(.show-more-btn)')
        
    if not round_buttons:
        # If still no buttons, maybe there's just one list
        round_buttons = [None]

    round_count = len(round_buttons)
    console.print(f"  [dim]{round_count} tur/grup bulundu.[/dim]")

    for i in range(round_count):
        if round_buttons[i]:
            # Refetch buttons to avoid stale element reference
            round_buttons = page.eles(round_selector) or page.eles('.transfer-league-btn:not(.show-more-btn)')
            if i >= len(round_buttons): break
            
            btn = round_buttons[i]
            btn_text = btn.text
            console.print(f"  [yellow]➤ {btn_text} yükleniyor...[/yellow]")
            
            try:
                # Use JS click to bypass visibility/scroll issues in horizontal container
                btn.click(by_js=True)
                time.sleep(2.5) # Increased wait for AJAX load
                
                # Double check if any matches appeared, if not, try one more click
                if not page.ele('xpath://div[@data-hid_match_id]', timeout=2):
                    console.print(f"    [dim]Yeniden deneniyor ({btn_text})...[/dim]")
                    btn.click(by_js=True)
                    time.sleep(2.5)
            except Exception as e:
                console.print(f"  [red]Buton tıklanamadı: {e}[/red]")
                continue
        else:
            console.print("  [yellow]➤ Maç listesi yükleniyor...[/yellow]")

        # Handle "Show More" pagination with robust wait
        show_more_count = 0
        while True:
            show_more = page.ele('.show-more-btn', timeout=1.5)
            if show_more and show_more.is_displayed:
                last_count = len(page.eles('xpath://div[@data-hid_match_id]'))
                try:
                    # Scroll and JS click just in case
                    page.scroll.to_see(show_more)
                    show_more.click(by_js=True)
                    
                    # Wait for items to increase (max 5 seconds)
                    wait_start = time.time()
                    while time.time() - wait_start < 5:
                        new_count = len(page.eles('xpath://div[@data-hid_match_id]'))
                        if new_count > last_count:
                            break
                        time.sleep(0.5)
                    
                    if len(page.eles('xpath://div[@data-hid_match_id]')) <= last_count:
                        # If count didn't increase after 5s, button might be stuck
                        break
                    
                    show_more_count += 1
                except Exception:
                    break
            else:
                break

        # Scrape match boxes in current round
        match_boxes = page.eles('xpath://div[@data-hid_match_id]')
        round_match_count = 0
        
        for box in match_boxes:
            match_id = box.attr('data-hid_match_id')
            if not match_id or match_id in seen_match_ids:
                continue
            
            seen_match_ids.add(match_id)
            
            get_attr = lambda b, a: b.attr(a) or ""
            
            match_data = {
                "match_id": match_id,
                "tournament": tournament_name,
                "round": get_attr(box, 'data-hid_round_name'),
                "date_timestamp": get_attr(box, 'data-hid_date'),
                "date_str": "",
                "home_team": get_attr(box, 'data-hid_host_name'),
                "away_team": get_attr(box, 'data-hid_guest_name'),
                "home_sets": get_attr(box, 'data-hid_host_sets'),
                "away_sets": get_attr(box, 'data-hid_guest_sets'),
                "venue": get_attr(box, 'data-hid_arena_name'),
            }
            
            if match_data["home_sets"] != "" and match_data["away_sets"] != "":
                match_data["score"] = f"{match_data['home_sets']}:{match_data['away_sets']}"
            else:
                match_data["score"] = "v"
            
            try:
                date_el = box.ele('t:time', timeout=0.1)
                if date_el:
                    match_data["date_str"] = date_el.text
            except Exception:
                pass

            all_matches.append(match_data)
            round_match_count += 1
            
        console.print(f"    [green]✓ {round_match_count} maç eklendi (Genişletme: {show_more_count}).[/green]")

    console.print(f"[bold green]✓ Toplam {len(all_matches)} maç çekildi.[/bold green]")
    return all_matches
