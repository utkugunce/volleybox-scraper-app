"""Debug script to see what DrissionPage sees on the matches page."""
from scraper.core import VolleyboxScraper
import time

with VolleyboxScraper() as scraper:
    page = scraper._get_page()
    url = "https://women.volleybox.net/women-turkiye-kadnlar-voleybol-2-ligi-2025-26-o38677/matches"
    page.get(url)
    scraper._wait_for_cloudflare()
    
    time.sleep(5) # Give it plenty of time
    
    print(f"URL loaded: {page.url}")
    print(f"Title: {page.title}")
    
    # All buttons
    btns = page.eles('t:button')
    print(f"Total buttons: {len(btns)}")
    for i, b in enumerate(btns[:20]):
        print(f"  Btn {i}: Class='{b.attr('class')}', Text='{b.text}'")
        
    # All divs with match in class
    match_divs = page.eles('.match_box')
    print(f"Total .match_box: {len(match_divs)}")
    
    if not match_divs:
        # Try broader search
        match_divs = page.eles('xpath://div[contains(@class, "match")]')
        print(f"Total div[contains(@class, 'match')]: {len(match_divs)}")
        
    # Check for hidden match IDs
    hids = page.eles('xpath://div[@data-hid_match_id]')
    print(f"Total divs with data-hid_match_id: {len(hids)}")
    
    # Check for Show More
    show_more = page.ele('.show-more-btn')
    print(f"Show more button found: {show_more is not None}")
    if show_more:
        print(f"  Displayed: {show_more.is_displayed}")
        print(f"  Class: {show_more.attr('class')}")

    # Save screenshot to see what's happening
    page.get_screenshot("debug_matches_state.png")
    print("Saved screenshot to debug_matches_state.png")
