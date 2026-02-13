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
    Scrape a single tournament/league detail page using DrissionPage directly.
    Navigates to the main page for name/teams and to /table for standings.

    Args:
        scraper: VolleyboxScraper instance
        url: Tournament URL

    Returns:
        Dict with detailed tournament info
    """
    console.print(f"[bold cyan]🏆 Turnuva detayı çekiliyor: {url}[/bold cyan]")

    page = scraper._get_page()
    page.get(url)

    # Wait for Cloudflare
    if not scraper._wait_for_cloudflare():
        console.print("[red]Cloudflare geçilemedi.[/red]")
        return None

    time.sleep(2)
    tournament = {"url": url}

    # --- Name (h1.dInline.marginRight10 or just h1) ---
    try:
        name_el = page.ele('t:h1')
        if name_el:
            tournament["name"] = name_el.text.strip()
            console.print(f"  Turnuva adı: {tournament['name']}")
    except Exception:
        tournament["name"] = "N/A"

    # --- Extract season from name ---
    name = tournament.get("name", "")
    import re as re_mod
    season_match = re_mod.search(r'(\d{4}/\d{2,4})', name)
    if season_match:
        tournament["season"] = season_match.group(1)

    # --- Teams from classification section ---
    teams = []
    try:
        team_links = page.eles('xpath://a[contains(@href, "-t") and contains(@href, "/tr/")]')
        for link in team_links:
            href = link.attr('href') or ''
            text = link.text.strip() if link.text else ''
            if re.search(r'-t\d+$', href) and text and len(text) > 1:
                full_url = href if href.startswith('http') else f"https://women.volleybox.net{href}"
                teams.append({"name": text, "url": full_url})
    except Exception as e:
        console.print(f"  [yellow]Takım çekme hatası: {e}[/yellow]")

    # Deduplicate teams
    seen = set()
    unique_teams = []
    for t in teams:
        if t["url"] not in seen:
            seen.add(t["url"])
            unique_teams.append(t)
    teams = unique_teams

    if teams:
        tournament["teams"] = teams
        tournament["team_count"] = len(teams)
        console.print(f"  {len(teams)} takım bulundu")

    # --- Navigate to /table for standings ---
    table_url = url.rstrip('/') + '/table'
    console.print(f"  Puan tablosu çekiliyor: {table_url}")

    try:
        page.get(table_url)
        if not scraper._wait_for_cloudflare():
            console.print("[yellow]  /table sayfasında Cloudflare geçilemedi[/yellow]")
        else:
            time.sleep(3)

            # Get the HTML and parse with BeautifulSoup
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page.html, "lxml")

            standings = []
            # Volleybox uses div-based tables, not <table> elements
            # Structure: div.tournament-table-container > h3.tournament-table-name + div.team
            containers = soup.select("div.tournament-table-container")
            console.print(f"  {len(containers)} grup tablosu bulundu")

            for container in containers:
                # Group name
                group_h3 = container.select_one("h3.tournament-table-name")
                group_name = group_h3.get_text(strip=True) if group_h3 else "N/A"

                # Team rows: div.team.top_dotted_line
                team_rows = container.select("div.team.top_dotted_line")
                for row in team_rows:
                    row_data = {"group": group_name}

                    # Rank
                    place_el = row.select_one("div.team_place")
                    if place_el:
                        row_data["sıra"] = place_el.get_text(strip=True)

                    # Team name (from a.title link)
                    name_link = row.select_one("a.title")
                    if name_link:
                        row_data["takım"] = name_link.get_text(strip=True)
                        href = name_link.get("href", "")
                        row_data["team_url"] = href if href.startswith("http") else f"https://women.volleybox.net{href}"

                    # Points
                    points_el = row.select_one("div.team_points")
                    if points_el:
                        row_data["puan"] = points_el.get_text(strip=True)

                    # Wins
                    won_el = row.select_one("div.team_won_matches")
                    if won_el:
                        row_data["galibiyet"] = won_el.get_text(strip=True)

                    # Losses
                    lost_el = row.select_one("div.team_lost_matches")
                    if lost_el:
                        row_data["mağlubiyet"] = lost_el.get_text(strip=True)

                    # Sets won
                    won_sets_el = row.select_one("div.team_won_sets")
                    if won_sets_el:
                        row_data["kazanılan_set"] = won_sets_el.get_text(strip=True)

                    # Sets lost
                    lost_sets_el = row.select_one("div.team_lost_sets")
                    if lost_sets_el:
                        row_data["kaybedilen_set"] = lost_sets_el.get_text(strip=True)

                    if row_data.get("takım"):
                        standings.append(row_data)

            if standings:
                tournament["standings"] = standings
                console.print(f"  [green]{len(standings)} sıralama satırı bulundu[/green]")
            else:
                console.print("  [yellow]Puan tablosu bulunamadı[/yellow]")

    except Exception as e:
        console.print(f"  [yellow]Puan tablosu hatası: {e}[/yellow]")

    # --- Extract country from tournament name ---
    name_text = tournament.get("name", "").lower()
    if "türkiye" in name_text or "turkiye" in name_text:
        tournament["country"] = "Türkiye"
    elif "turkey" in name_text:
        tournament["country"] = "Turkey"

    console.print(f"[bold green]✓ Turnuva çekildi: {tournament.get('name', 'N/A')}[/bold green]")
    return tournament


def scrape_tournament_matches(scraper, url, progress_callback=None):
    """
    Scrape all matches from a tournament matches page.
    Handles multiple rounds and 'Show More' pagination using browser interaction.

    Args:
        scraper: VolleyboxScraper instance
        url: Tournament matches URL
        progress_callback: Optional callable(round_index, round_count, match_count, round_name)

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
    if progress_callback:
        progress_callback(0, round_count, 0, "Hazırlanıyor...")

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
        if progress_callback:
            progress_callback(i + 1, round_count, len(all_matches), btn_text if round_buttons[i] else f"Tur {i+1}")

    console.print(f"[bold green]✓ Toplam {len(all_matches)} maç çekildi.[/bold green]")
    return all_matches
