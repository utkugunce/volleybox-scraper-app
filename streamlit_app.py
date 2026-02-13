import streamlit as st
import pandas as pd
import altair as alt
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

# Custom CSS for Premium Look
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background-color: #0f172a;
    }
    
    /* Headings */
    h1, h2, h3 {
        color: #f8fafc !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Metrics */
    div[data-testid="stMetric"] {
        background-color: #1e293b;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid rgba(148, 163, 184, 0.1);
    }
    
    /* Cards (Container) */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        # background-color: #1e293b;
        # padding: 1.5rem;
        # border-radius: 0.5rem;
        # border: 1px solid rgba(148, 163, 184, 0.1);
    }

    /* Buttons */
    .stButton>button {
        background-color: #8b5cf6;
        color: white;
        border: none;
        border-radius: 0.375rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #7c3aed;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #020617;
        border-right: 1px solid #1e293b;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for scraper
if 'scraper' not in st.session_state:
    st.session_state.scraper = VolleyboxScraper(headless=True)

def get_scraper():
    return st.session_state.scraper

# Helper to clear detail view state when switching main pages
def clear_detail_state():
    if 'selected_team_url' in st.session_state:
        del st.session_state.selected_team_url

# Sidebar Navigation
with st.sidebar:
    st.title("🏐 Volleybox")
    st.caption("Premium Scraper Interface")
    
    page = st.radio(
        "Navigation", 
        ["Dashboard", "Teams", "Players", "Tournaments"],
        index=0,
        on_change=clear_detail_state
    )
    
    st.divider()
    st.info("Data source: women.volleybox.net")
    
    if st.button("Reset Scraper Check"):
        st.session_state.scraper = VolleyboxScraper(headless=True)
        st.success("Scraper re-initialized!")

# --- DASHBOARD ---
if page == "Dashboard":
    st.title("Dashboard")
    st.markdown("### Welcome to Volleybox Scraper")
    st.write("Browse comprehensive data from the world of women's volleyball.")
    
    # Fake metrics for visual appeal (since we don't database everything yet)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Active Teams", value="2,500+", delta="Live")
    with col2:
        st.metric(label="Players Tracked", value="15,000+", delta="Live")
    with col3:
        st.metric(label="Tournaments", value="100+", delta="Live")
    with col4:
        st.metric(label="Status", value="Online", delta_color="normal")
        
    st.markdown("---")
    
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.subheader("Recent Activity")
        st.info("Start browsing by selecting a category from the sidebar.")
        
    with col_right:
        st.subheader("Quick Actions")
        if st.button("Scrape Top Teams"):
            st.session_state.quick_scrape = True
            st.rerun()

# --- TEAMS ---
elif page == "Teams":
    st.title("Teams")

    # Team State Handling
    if 'teams' not in st.session_state:
        st.session_state.teams = []
        
    if 'selected_team_url' in st.session_state:
        # --- TEAM DETAIL VIEW ---
        url = st.session_state.selected_team_url
        if st.button("← Back to List"):
            del st.session_state.selected_team_url
            st.rerun()
            
        with st.spinner(f"Scraping team details from {url}..."):
            # Cache scraping result in session for short term
            cache_key = f"team_detail_{url}"
            if cache_key not in st.session_state:
                scraper = get_scraper()
                try:
                    detail = scrape_team_profile(scraper, url)
                    st.session_state[cache_key] = detail
                except Exception as e:
                    st.error(f"Failed to scrape team: {str(e)}")
                    st.stop()
            
            detail = st.session_state[cache_key]
            
            # Header
            st.header(detail.get('name', 'Unknown Team'))
            st.caption(f"{detail.get('country', '')} • {detail.get('league', '')}")
            
            # Roster Analysis
            if detail.get('roster'):
                st.subheader("Roster")
                df = pd.DataFrame(detail['roster'])
                
                # Filters
                positions = ["All"] + list(df['position'].unique()) if 'position' in df.columns else []
                selected_pos = st.selectbox("Filter Position", positions)
                
                if selected_pos != "All":
                    df_display = df[df['position'] == selected_pos]
                else:
                    df_display = df
                
                # Display Styled Table
                st.dataframe(
                    df_display,
                    column_config={
                        "player_name": "Player",
                        "position": "Position",
                        "height": st.column_config.NumberColumn("Height", format="%d cm"),
                        "age": st.column_config.NumberColumn("Age"),
                        "number": "No."
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                # Visualizations
                st.subheader("Team Analysis")
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    if 'height' in df.columns:
                        # Convert height to numeric
                        df['height_num'] = pd.to_numeric(df['height'].astype(str).str.replace('cm', ''), errors='coerce')
                        chart_height = alt.Chart(df).mark_bar().encode(
                            x=alt.X('player_name', sort='-y', title='Player'),
                            y=alt.Y('height_num', title='Height (cm)'),
                            color=alt.Color('position', legend=None),
                            tooltip=['player_name', 'height_num', 'position']
                        ).properties(title="Player Heights")
                        st.altair_chart(chart_height, use_container_width=True)
                        
                with col_chart2:
                    if 'position' in df.columns:
                        chart_pos = alt.Chart(df).mark_arc().encode(
                            theta=alt.Theta("count()", stack=True),
                            color=alt.Color("position"),
                            tooltip=["position", "count()"]
                        ).properties(title="Position Distribution")
                        st.altair_chart(chart_pos, use_container_width=True)

    else:
        # --- TEAM LIST VIEW ---
        col_search, col_action = st.columns([3, 1])
        with col_search:
            search_query = st.text_input("Search Teams (not live regex yet)")
        with col_action:
            if st.button("Load/Refresh List", type="primary"):
                with st.spinner("Fetching latest team list..."):
                    scraper = get_scraper()
                    st.session_state.teams = scrape_team_list(scraper, page_limit=1)

        if st.session_state.teams:
            # Grid Layout
            cols = st.columns(3)
            for idx, team in enumerate(st.session_state.teams):
                with cols[idx % 3]:
                    with st.container():
                        st.markdown(f"#### {team['name']}")
                        st.text(f"{team.get('country', '')}\n{team.get('league', '')}")
                        if st.button("View Details", key=f"btn_team_{idx}"):
                            st.session_state.selected_team_url = team['url']
                            st.rerun()
                        st.divider()

# --- PLAYERS ---
elif page == "Players":
    st.title("Players")
    if st.button("Load Players List"):
         with st.spinner("Fetching players..."):
            scraper = get_scraper()
            st.session_state.players = scrape_player_list(scraper, page_limit=1)
            
    if 'players' in st.session_state:
        df_players = pd.DataFrame(st.session_state.players)
        st.dataframe(
            df_players,
            column_config={
                "name": "Name",
                "position": "Position", 
                "country": "Country"
            },
            use_container_width=True
        )

# --- TOURNAMENTS ---
elif page == "Tournaments":
    st.title("Tournaments")
    
    tab_list, tab_scrape = st.tabs(["Browse List", "Scrape by URL"])
    
    with tab_list:
        if st.button("Load Tournaments"):
             with st.spinner("Fetching tournaments..."):
                scraper = get_scraper()
                st.session_state.tournaments = scrape_tournament_list(scraper, page_limit=1)
        
        if 'tournaments' in st.session_state:
            for tourney in st.session_state.tournaments:
                with st.expander(tourney.get('name', 'Tournament')):
                    st.write(f"Season: {tourney.get('season', '2024/25')}")
                    st.write(f"Link: {tourney.get('url', '#')}")
    
    with tab_scrape:
        st.subheader("Scrape Specific Tournament")
        tourney_url = st.text_input("Enter Tournament URL", placeholder="https://women.volleybox.net/...")
        
        if st.button("Scrape Tournament Data"):
            if not tourney_url:
                st.warning("Please enter a URL first.")
            else:
                try:
                    scraper = get_scraper()
                    
                    # 1. Scrape Info & Standings
                    with st.status("Scraping tournament data...", expanded=True) as status:
                        status.write("Fetching details & standings...")
                        detail = scrape_tournament_detail(scraper, tourney_url)
                        st.session_state.current_tournament = detail
                        
                        status.write("Fetching matches (this may take a while)...")
                        # Construct matches URL (usually just append /matches or similar, but for now let's hope the scraper handles it or we use the detail)
                        # Actually scrape_tournament_matches needs a specific matches URL mostly.
                        # Let's try to deduce it or check if 'matches' key exists in detail (it does for recent/few matches)
                        
                        # If the user provided a main tournament page, scrape_tournament_detail gets basic info + matches displayed there
                        # If we want ALL matches, we might need to find the "matches" link in the detail and scrape that.
                        
                        status.update(label="Scraping complete!", state="complete", expanded=False)
                    
                    if detail:
                        st.success(f"Loaded: {detail.get('name')}")
                        
                        # Basic Info
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Season", detail.get('season', 'N/A'))
                        col2.metric("Teams", detail.get('team_count', 'N/A'))
                        col3.metric("Country", detail.get('country', 'N/A'))
                        
                        # Standings
                        if detail.get('standings'):
                            st.subheader("Standings")
                            st.dataframe(detail['standings'], use_container_width=True)
                        
                        # Matches
                        if detail.get('matches'):
                            st.subheader("Matches")
                            st.dataframe(detail['matches'], use_container_width=True)
                        else:
                            st.info("No matches found on the main page. Try the matches tab link if available.")
                            
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")


