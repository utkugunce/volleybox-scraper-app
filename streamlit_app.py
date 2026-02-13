import streamlit as st
import sys
import os
import time

# Add repository root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.core import VolleyboxScraper
from scraper.teams import scrape_team_list, scrape_team_profile
from scraper.players import scrape_player_list, scrape_player_profile
from scraper.tournaments import scrape_tournament_list, scrape_tournament_detail

# Page config
st.set_page_config(
    page_title="Volleybox Scraper",
    page_icon="🏐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .stCard {
        background-color: #1e293b;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid rgba(148, 163, 184, 0.1);
    }
    h1, h2, h3 {
        color: #f8fafc !important;
    }
    p, label {
        color: #94a3b8 !important;
    }
    .stButton>button {
        background-color: #8b5cf6;
        color: white;
        border: none;
    }
    .stButton>button:hover {
        background-color: #7c3aed;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for scraper
if 'scraper' not in st.session_state:
    st.session_state.scraper = VolleyboxScraper(headless=True) # Headless for Streamlit Cloud

def get_scraper():
    return st.session_state.scraper

# Sidebar
st.sidebar.title("🏐 Volleybox")
page = st.sidebar.radio("Navigate", ["Dashboard", "Teams", "Players", "Tournaments"])

st.sidebar.divider()
st.sidebar.info("Data scraped live from women.volleybox.net")

# Dashboard
if page == "Dashboard":
    st.title("🏐 Volleybox Scraper Dashboard")
    st.markdown("""
    Welcome to the Volleybox Scraper interface. 
    Select a category from the sidebar to browse data.
    """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="stCard"><h3>Teams</h3><p>Browse detailed club statistics</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="stCard"><h3>Players</h3><p>View profiles and careers</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="stCard"><h3>Tournaments</h3><p>Leagues and cups info</p></div>', unsafe_allow_html=True)

# Teams
elif page == "Teams":
    st.title("Teams")
    
    tab1, tab2 = st.tabs(["List", "Detail"])
    
    with tab1:
        if st.button("Load Teams"):
            with st.spinner("Fetching teams..."):
                scraper = get_scraper()
                teams = scrape_team_list(scraper, page_limit=1)
                st.session_state.teams = teams
        
        if 'teams' in st.session_state:
            for team in st.session_state.teams:
                with st.container():
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if team.get('logo_url'):
                            st.image(team['logo_url'], width=100)
                    with col2:
                        st.subheader(team['name'])
                        st.text(f"{team.get('country', '')} | {team.get('league', '')}")
                        if st.button("View Detail", key=f"btn_{team['url']}"):
                            st.session_state.selected_team_url = team['url']
                            st.experimental_rerun()
                    st.divider()

    with tab2:
        url = st.text_input("Team URL", value=st.session_state.get('selected_team_url', ''))
        if st.button("Scrape Profile"):
            if url:
                with st.spinner("Scraping profile..."):
                    scraper = get_scraper()
                    detail = scrape_team_profile(scraper, url)
                    st.json(detail)
                    
                    if detail.get('roster'):
                        st.subheader("Roster")
                        st.dataframe(detail['roster'])

# Players
elif page == "Players":
    st.title("Players")
    if st.button("Load Players"):
         with st.spinner("Fetching players..."):
            scraper = get_scraper()
            players = scrape_player_list(scraper, page_limit=1)
            st.dataframe(players)

# Tournaments
elif page == "Tournaments":
    st.title("Tournaments")
    if st.button("Load Tournaments"):
         with st.spinner("Fetching tournaments..."):
            scraper = get_scraper()
            tournaments = scrape_tournament_list(scraper, page_limit=1)
            st.dataframe(tournaments)

