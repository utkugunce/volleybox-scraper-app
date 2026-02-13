"""
Core scraper module for women.volleybox.net
Uses DrissionPage (real Chromium browser) to bypass Cloudflare protection.
Uses a persistent user data directory to maintain session and improve Cloudflare bypass success.
"""

import os
import time
import random
from bs4 import BeautifulSoup
from DrissionPage import ChromiumPage, ChromiumOptions
from rich.console import Console

console = Console()

BASE_URL = "https://women.volleybox.net"
DEFAULT_LANG = "tr"
# Persistent user data directory
USER_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "browser_data")


class VolleyboxScraper:
    """Main scraper engine for women.volleybox.net with Cloudflare bypass."""

    def __init__(self, lang=DEFAULT_LANG, delay=(2.0, 4.0), max_retries=3, headless=False):
        self.lang = lang
        self.delay = delay
        self.max_retries = max_retries
        self.headless = headless
        self._page = None
        self._last_request_time = 0

    def _get_page(self):
        """Get or create the browser page instance."""
        if self._page is None:
            console.print("[dim]🌐 Tarayıcı başlatılıyor...[/dim]")
            co = ChromiumOptions()

            # Robust anti-detection and persistence settings
            co.set_argument("--no-sandbox")
            co.set_argument("--disable-blink-features=AutomationControlled")
            co.set_argument("--disable-infobars")
            co.set_argument(f"--user-data-dir={USER_DATA_DIR}")  # Persistent session
            co.set_argument("--lang=tr-TR")
            
            # Randomize window size slightly to look human
            width = random.randint(1200, 1400)
            height = random.randint(800, 1000)
            co.set_argument(f"--window-size={width},{height}")

            if self.headless:
                co.headless()

            self._page = ChromiumPage(co)

            # Additional CDP overrides to hide automation
            try:
                self._page.run_cdp("Page.addScriptToEvaluateOnNewDocument", source="""
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                """)
            except Exception:
                pass

            console.print("[dim]✓ Tarayıcı hazır[/dim]")
        return self._page

    def _is_cloudflare_page(self, html=None):
        """Check if the current page is a Cloudflare challenge."""
        page = self._get_page()
        
        # Check for positive success indicators first
        try:
            title = page.title or ""
            if "volleybox" in title.lower() or "voleybol" in title.lower():
                return False
        except Exception:
            pass

        if html is None:
            try:
                html = page.html or ""
            except Exception:
                return True
        
        html_lower = html.lower()
        
        # If we have substantial content and volleybox keywords, it's likely not a challenge page
        if len(html) > 5000 and ("volleybox" in html_lower or "transfer" in html_lower):
            return False
        
        # Simple checks for Cloudflare title/content
        if "just a moment" in html_lower or "bir dakika" in html_lower:
            return True
        if "cloudflare" in html_lower and "challenge" in html_lower:
            return True
            
        return False

    def _wait_for_cloudflare(self, timeout=120):
        """
        Wait for Cloudflare challenge to resolve. 
        Prompts user if needed.
        """
        page = self._get_page()
        start = time.time()
        
        # Initial check
        if not self._is_cloudflare_page(page.html or ""):
            return True

        console.print("  [yellow]⏳ Cloudflare kontrolü yapılıyor...[/yellow]")
        
        # Try auto-wait first
        while time.time() - start < 15:
            if not self._is_cloudflare_page(page.html or ""):
                console.print("  [green]✓ Cloudflare geçildi![/green]")
                return True
            time.sleep(1)

        # Prompt user interaction
        console.print("[bold yellow]⚠ Lütfen açılan pencerede Cloudflare doğrulamasını tamamlayın![/bold yellow]")
        
        while time.time() - start < timeout:
            if not self._is_cloudflare_page(page.html or ""):
                console.print("  [green]✓ Cloudflare geçildi![/green]")
                return True
            time.sleep(2)
        
        return False

    def get_page(self, url, params=None):
        """Fetch a page."""
        if url.startswith("/"):
            url = f"{BASE_URL}{url}"
        
        if params:
            param_str = "&".join(f"{k}={v}" for k, v in params.items())
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{param_str}"

        page = self._get_page()

        for attempt in range(1, self.max_retries + 1):
            try:
                # Rate limit
                elapsed = time.time() - self._last_request_time
                wait = random.uniform(*self.delay)
                if elapsed < wait:
                    time.sleep(wait - elapsed)

                console.print(f"  [dim]Fetching: {url}[/dim]")
                page.get(url)
                self._last_request_time = time.time()
                
                # Check Cloudflare
                if not self._wait_for_cloudflare():
                    console.print("  [red]Cloudflare geçilemedi.[/red]")
                    continue

                html = page.html
                if html:
                    return BeautifulSoup(html, "lxml")

            except Exception as e:
                console.print(f"  [red]Hata: {e}[/red]")
                
        return None

    def build_url(self, path=""):
        path = path.lstrip("/")
        return f"{BASE_URL}/{self.lang}/{path}"

    def close(self):
        if self._page:
            try:
                self._page.quit()
            except Exception:
                pass
            self._page = None
            console.print("[dim]🌐 Tarayıcı kapatıldı[/dim]")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
