"""
Transfer scraping module for women.volleybox.net
Handles scraping of transfer/market data.
"""

import re
from rich.console import Console

console = Console()


def _extract_team_name(link):
    """
    Extract team name from a link element.
    Falls back to URL parsing if text is empty (e.g., when link contains only a logo image).
    """
    name = link.get_text(strip=True)
    if name:
        return name

    # Try image alt text
    img = link.select_one("img")
    if img:
        alt = img.get("alt", "").strip()
        if alt:
            return alt
        title = img.get("title", "").strip()
        if title:
            return title

    # Extract from URL: /tr/team-name-here-t12345 → Team Name Here
    href = link.get("href", "")
    match = re.search(r'/([^/]+)-t\d+$', href)
    if match:
        slug = match.group(1)
        # Convert slug to title case
        return slug.replace("-", " ").title()

    return ""


def _make_full_url(href):
    """Convert relative URL to full URL."""
    if not href:
        return ""
    if href.startswith("http"):
        return href
    return f"https://women.volleybox.net{href}"

def scrape_transfers(scraper, page_limit=3):
    """
    Scrape transfer data from the homepage and transfer page.

    Args:
        scraper: VolleyboxScraper instance
        page_limit: Max pages of transfers to scrape

    Returns:
        List of dicts with transfer info
    """
    transfers = []

    console.print("[bold cyan]📋 Transfer verileri çekiliyor...[/bold cyan]")

    # --- Homepage transfers ---
    soup = scraper.get_page(scraper.build_url(""))
    if soup:
        _extract_transfers_from_page(soup, transfers)

    # --- Dedicated transfer page ---
    for page in range(1, page_limit + 1):
        url = scraper.build_url("transfers")
        params = {"page": page} if page > 1 else None
        soup = scraper.get_page(url, params=params)

        if not soup:
            break

        before_count = len(transfers)
        _extract_transfers_from_page(soup, transfers)

        if len(transfers) == before_count:
            # No new transfers found, stop
            break

        console.print(f"  [green]Sayfa {page}: {len(transfers) - before_count} transfer bulundu[/green]")

    # Deduplicate
    seen = set()
    unique_transfers = []
    for t in transfers:
        key = f"{t.get('player_url', '')}|{t.get('from_team_url', '')}|{t.get('to_team_url', '')}"
        if key not in seen:
            seen.add(key)
            unique_transfers.append(t)

    console.print(f"[bold green]✓ Toplam {len(unique_transfers)} transfer bulundu[/bold green]")
    return unique_transfers


def _extract_transfers_from_page(soup, transfers):
    """Extract transfer data from a page's HTML."""

    # Look for transfer sections/containers
    transfer_sections = soup.select(
        ".transfer-item, .transfer-row, .transfer-card, "
        ".market-item, .transfer-list li, .transfer-list > div"
    )

    if transfer_sections:
        for item in transfer_sections:
            transfer = _parse_transfer_item(item)
            if transfer:
                transfers.append(transfer)
        return

    # Fallback: Look for player links with team context
    # Transfer pattern: [Player] [From Team] >> [To Team]
    all_links = soup.select("a")
    i = 0
    while i < len(all_links):
        link = all_links[i]
        href = link.get("href", "")

        # If this is a player link
        if re.search(r'-p\d+$', href):
            player_name = link.get_text(strip=True)
            player_url = href if href.startswith("http") else f"https://women.volleybox.net{href}"

            # Look at surrounding elements for team info
            parent = link.parent
            if parent:
                grandparent = parent.parent
            else:
                grandparent = None

            context = grandparent if grandparent else parent if parent else link.parent

            if context:
                # Find team links near this player
                team_links = context.select("a[href*='-t']")
                from_team = ""
                from_team_url = ""
                to_team = ""
                to_team_url = ""

                if len(team_links) >= 2:
                    from_team = _extract_team_name(team_links[0])
                    from_team_url = _make_full_url(team_links[0].get("href", ""))
                    to_team = _extract_team_name(team_links[1])
                    to_team_url = _make_full_url(team_links[1].get("href", ""))
                elif len(team_links) == 1:
                    to_team = _extract_team_name(team_links[0])
                    to_team_url = _make_full_url(team_links[0].get("href", ""))

                # Find position/nationality info
                position = ""
                nationality = ""
                text_parts = context.get_text(separator="|", strip=True).split("|")
                for part in text_parts:
                    part = part.strip()
                    if part and part != player_name and part != from_team and part != to_team:
                        if not position and len(part) < 30:
                            # Check if it looks like position info
                            if any(pos in part.lower() for pos in [
                                "pasör", "smaçör", "orta", "libero", "setter", "opposite",
                                "middle", "outside", "blocker", "hitter", "çaprazı"
                            ]):
                                position = part
                            elif "-" in part and len(part) < 30:
                                # Likely "Position - Country" format
                                pos_parts = part.split("-")
                                position = pos_parts[0].strip()
                                if len(pos_parts) > 1:
                                    nationality = pos_parts[1].strip()

                if player_name:
                    transfer_data = {
                        "player_name": player_name,
                        "player_url": player_url,
                        "from_team": from_team,
                        "from_team_url": from_team_url,
                        "to_team": to_team,
                        "to_team_url": to_team_url,
                        "position": position,
                        "nationality": nationality,
                    }
                    transfers.append(transfer_data)

        i += 1


def _parse_transfer_item(item):
    """Parse a single transfer item element."""
    transfer = {}

    # Player
    player_link = item.select_one("a[href*='-p']")
    if player_link:
        name = player_link.get_text(strip=True)
        if not name or name.startswith("http"):
            # Try title or image alt
            name = player_link.get("title", "").strip()
            if not name:
                img = player_link.select_one("img")
                if img:
                    name = img.get("alt", "").strip() or img.get("title", "").strip()
        
        transfer["player_name"] = name
        href = player_link.get("href", "")
        transfer["player_url"] = href if href.startswith("http") else f"https://women.volleybox.net{href}"

    # Teams
    team_links = item.select("a[href*='-t']")
    if len(team_links) >= 2:
        transfer["from_team"] = _extract_team_name(team_links[0])
        transfer["from_team_url"] = _make_full_url(team_links[0].get("href", ""))
        transfer["to_team"] = _extract_team_name(team_links[1])
        transfer["to_team_url"] = _make_full_url(team_links[1].get("href", ""))
    elif len(team_links) == 1:
        transfer["to_team"] = _extract_team_name(team_links[0])
        transfer["to_team_url"] = _make_full_url(team_links[0].get("href", ""))

    # Position info
    position_el = item.select_one(".position, .player-position")
    if position_el:
        transfer["position"] = position_el.get_text(strip=True)

    # Date
    date_el = item.select_one(".date, .transfer-date, time")
    if date_el:
        transfer["date"] = date_el.get_text(strip=True)

    return transfer if transfer.get("player_name") else None
