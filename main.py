"""
Volleybox Scraper — CLI Tool
women.volleybox.net sitesinden veri çekme aracı.

Kullanım:
    python main.py players --list                       # Oyuncu listesi
    python main.py players --url <url>                  # Tek oyuncu detayı
    python main.py players --list --detail              # Oyuncu listesi + detaylar
    python main.py teams --list                         # Takım listesi
    python main.py teams --url <url>                    # Tek takım detayı
    python main.py teams --url <url> --roster           # Takım kadrosu (flat list)
    python main.py tournaments --list                   # Turnuva listesi
    python main.py tournaments --url <url>              # Turnuva detayı
    python main.py transfers                            # Transferler
    python main.py search <arama terimi>                # Sitede arama

Ortak opsiyonlar:
    --format json|csv|excel                             # Export formatı (default: json)
    --output <dosya>                                    # Çıktı dosya adı
    --lang tr|en                                        # Site dili (default: tr)
    --pages <n>                                         # Sayfa limiti (default: 5)
    --limit <n>                                         # Detay limiti (default: 10)
"""

import argparse
import sys
from rich.console import Console
from rich.panel import Panel

from scraper.core import VolleyboxScraper
from scraper.players import scrape_player_list, scrape_player_profile, scrape_players_detail
from scraper.teams import scrape_team_list, scrape_team_profile, scrape_teams_detail
from scraper.tournaments import scrape_tournament_list, scrape_tournament_detail
from scraper.transfers import scrape_transfers
from scraper.exporter import export_data, print_summary

console = Console()


def search_site(scraper, query):
    """Search the site using the search bar."""
    console.print(f"[bold cyan]🔍 Aranıyor: {query}[/bold cyan]")

    url = f"https://women.volleybox.net/{scraper.lang}/search"
    soup = scraper.get_page(url, params={"q": query})

    if not soup:
        return []

    results = []

    # Find all result links
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

    console.print(f"[bold green]✓ {len(unique)} sonuç bulundu[/bold green]")
    return unique


def main():
    parser = argparse.ArgumentParser(
        description="🏐 Volleybox Scraper — women.volleybox.net veri çekme aracı",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", help="Komut seçin")

    # --- Players ---
    players_parser = subparsers.add_parser("players", help="Oyuncu verileri")
    players_parser.add_argument("--list", action="store_true", help="Oyuncu listesi çek")
    players_parser.add_argument("--url", type=str, help="Tek oyuncu profili URL")
    players_parser.add_argument("--detail", action="store_true", help="Liste + detay çek")

    # --- Teams ---
    teams_parser = subparsers.add_parser("teams", help="Takım verileri")
    teams_parser.add_argument("--list", action="store_true", help="Takım listesi çek")
    teams_parser.add_argument("--url", type=str, help="Tek takım profili URL")
    teams_parser.add_argument("--detail", action="store_true", help="Liste + detay çek")
    teams_parser.add_argument("--roster", action="store_true", help="Sadece oyuncu kadrosunu çek (Liste formatında)")

    # --- Tournaments ---
    tourn_parser = subparsers.add_parser("tournaments", help="Turnuva verileri")
    tourn_parser.add_argument("--list", action="store_true", help="Turnuva listesi çek")
    tourn_parser.add_argument("--url", type=str, help="Tek turnuva URL")
    tourn_parser.add_argument("--matches", action="store_true", help="Turnuva maçlarını çek")

    # --- Transfers ---
    transfer_parser = subparsers.add_parser("transfers", help="Transfer verileri")

    # --- Search ---
    search_parser = subparsers.add_parser("search", help="Sitede arama")
    search_parser.add_argument("query", type=str, help="Arama terimi")

    # --- Common options ---
    for p in [players_parser, teams_parser, tourn_parser, transfer_parser, search_parser]:
        p.add_argument("--format", choices=["json", "csv", "excel"], default="json", help="Export formatı")
        p.add_argument("--output", "-o", type=str, help="Çıktı dosya adı")
        p.add_argument("--lang", choices=["tr", "en"], default="tr", help="Site dili")
        p.add_argument("--pages", type=int, default=5, help="Sayfa limiti")
        p.add_argument("--limit", type=int, default=10, help="Detay çekilecek kayıt limiti")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Banner
    console.print(Panel.fit(
        "[bold white]🏐 Volleybox Scraper[/bold white]\n"
        "[dim]women.volleybox.net veri çekme aracı[/dim]",
        border_style="bright_magenta",
    ))

    # Create scraper with context manager for proper cleanup
    with VolleyboxScraper(lang=args.lang) as scraper:
        data = []

        # --- Execute command ---
        if args.command == "players":
            if args.url:
                result = scrape_player_profile(scraper, args.url)
                data = [result] if result else []
            elif args.list:
                data = scrape_player_list(scraper, page_limit=args.pages)
                if args.detail and data:
                    data = scrape_players_detail(scraper, data, limit=args.limit)
            else:
                console.print("[yellow]--list veya --url belirtin.[/yellow]")
                sys.exit(1)

        elif args.command == "teams":
            if args.url:
                result = scrape_team_profile(scraper, args.url)
                if result:
                    if args.roster:
                        # Extract roster as main data list
                        roster = result.get("roster", [])
                        team_name = result.get("name", "Unknown Team")
                        # Add team context
                        for p in roster:
                            p["team"] = team_name
                            p["team_url"] = args.url
                        data = roster
                    else:
                        data = [result]
                else:
                    data = []
            elif args.list:
                data = scrape_team_list(scraper, page_limit=args.pages)
                if args.detail and data:
                    data = scrape_teams_detail(scraper, data, limit=args.limit)
            else:
                console.print("[yellow]--list veya --url belirtin.[/yellow]")
                sys.exit(1)

        elif args.command == "tournaments":
            if args.url:
                if args.matches:
                    from scraper.tournaments import scrape_tournament_matches
                    data = scrape_tournament_matches(scraper, args.url)
                else:
                    result = scrape_tournament_detail(scraper, args.url)
                    data = [result] if result else []
            elif args.list:
                data = scrape_tournament_list(scraper, page_limit=args.pages)
            else:
                console.print("[yellow]--list veya --url belirtin.[/yellow]")
                sys.exit(1)

        elif args.command == "transfers":
            data = scrape_transfers(scraper, page_limit=args.pages)

        elif args.command == "search":
            data = search_site(scraper, args.query)

    # --- Output ---
    if data:
        print_summary(data, title=f"{args.command.upper()} Sonuçları")

        if args.output:
            export_data(data, args.output, format=args.format)
        else:
            default_name = f"volleybox_{args.command}"
            export_data(data, default_name, format=args.format)
    else:
        console.print("[yellow]⚠ Veri bulunamadı.[/yellow]")


if __name__ == "__main__":
    main()
