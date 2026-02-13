import streamlit as st
import pandas as pd
import altair as alt
import json
import io

# Page config
st.set_page_config(
    page_title="Volleybox Scraper",
    page_icon="🏐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-tertiary: #334155;
    --accent: #8b5cf6;
    --accent-hover: #7c3aed;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --border: rgba(148, 163, 184, 0.12);
    --success: #10b981;
    --warning: #f59e0b;
}

.stApp {
    background-color: var(--bg-primary);
    font-family: 'Inter', sans-serif;
}

h1, h2, h3, h4 {
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
}

/* Metrics */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
    padding: 1.2rem;
    border-radius: 0.75rem;
    border: 1px solid var(--border);
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.15);
}
div[data-testid="stMetric"] label {
    color: var(--text-secondary) !important;
    font-size: 0.85rem !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
    color: white;
    border: none;
    border-radius: 0.5rem;
    font-weight: 600;
    padding: 0.6rem 1.5rem;
    transition: all 0.3s ease;
    box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
}
.stButton>button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.5);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #020617;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .stRadio label {
    color: var(--text-secondary) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 0.5rem;
    padding: 0.5rem 1rem;
}

/* Expander */
.streamlit-expanderHeader {
    background-color: var(--bg-secondary) !important;
    border-radius: 0.5rem !important;
}

/* Dataframe */
.stDataFrame {
    border-radius: 0.5rem;
    overflow: hidden;
}

/* File uploader */
.stFileUploader {
    border: 2px dashed var(--accent) !important;
    border-radius: 0.75rem !important;
    padding: 1rem !important;
}

/* Hero Banner */
.hero-banner {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4c1d95 100%);
    padding: 2rem 2.5rem;
    border-radius: 1rem;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(139, 92, 246, 0.2);
}
.hero-banner h1 {
    margin: 0;
    font-size: 2rem;
}
.hero-banner p {
    color: #c4b5fd !important;
    margin-top: 0.5rem;
    font-size: 1.05rem;
}

/* Stat Card */
.stat-card {
    background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
    padding: 1.5rem;
    border-radius: 0.75rem;
    border: 1px solid var(--border);
    text-align: center;
}
.stat-card h2 {
    font-size: 2.5rem !important;
    color: var(--accent) !important;
    margin: 0;
}
.stat-card p {
    color: var(--text-secondary) !important;
    margin: 0.25rem 0 0 0;
    font-size: 0.9rem;
}

/* Info box */
.info-box {
    background-color: var(--bg-secondary);
    padding: 1.2rem 1.5rem;
    border-radius: 0.75rem;
    border-left: 4px solid var(--accent);
    margin: 1rem 0;
}
.info-box p { color: var(--text-secondary) !important; margin: 0; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🏐 Volleybox")
    st.caption("Data Visualization Dashboard")
    
    page = st.radio(
        "Navigation",
        ["Dashboard", "Match Explorer", "Team Analysis", "Upload Data"],
        index=0
    )
    
    st.divider()
    st.markdown("""
    <div class="info-box">
    <p><b>💡 Nasıl Kullanılır?</b><br>
    1. Lokal olarak scraper'ı çalıştırın<br>
    2. JSON dosyasını Upload Data sekmesinden yükleyin<br>
    3. Verileri analiz edin!</p>
    </div>
    """, unsafe_allow_html=True)


# ── Session State ───────────────────────────────────────────
if 'match_data' not in st.session_state:
    st.session_state.match_data = None
if 'match_df' not in st.session_state:
    st.session_state.match_df = None


def load_match_data(data):
    """Parse match JSON data into a DataFrame."""
    df = pd.DataFrame(data)
    
    # Clean up score column
    if 'score' in df.columns:
        df['score'] = df['score'].fillna('vs')
    
    # Parse date if available
    if 'date_str' in df.columns:
        df['date_str'] = df['date_str'].fillna('')
    
    # Create result column
    if 'home_sets' in df.columns and 'away_sets' in df.columns:
        df['home_sets'] = pd.to_numeric(df['home_sets'], errors='coerce')
        df['away_sets'] = pd.to_numeric(df['away_sets'], errors='coerce')
    
    return df


# ── DASHBOARD ───────────────────────────────────────────────
if page == "Dashboard":
    st.markdown("""
    <div class="hero-banner">
        <h1>🏐 Volleybox Scraper Dashboard</h1>
        <p>Kadın voleybolunun kapsamlı veri analiz platformu</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.match_df is not None:
        df = st.session_state.match_df
        
        # Summary Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Matches", f"{len(df):,}")
        with col2:
            teams = set()
            if 'home_team' in df.columns:
                teams.update(df['home_team'].dropna().unique())
            if 'away_team' in df.columns:
                teams.update(df['away_team'].dropna().unique())
            st.metric("Teams", f"{len(teams):,}")
        with col3:
            if 'round' in df.columns:
                st.metric("Rounds", f"{df['round'].nunique():,}")
            else:
                st.metric("Rounds", "N/A")
        with col4:
            if 'venue' in df.columns:
                st.metric("Venues", f"{df['venue'].nunique():,}")
            else:
                st.metric("Venues", "N/A")
        
        st.markdown("---")
        
        # Charts Row
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("Matches per Round")
            if 'round' in df.columns:
                round_counts = df['round'].value_counts().reset_index()
                round_counts.columns = ['Round', 'Count']
                chart = alt.Chart(round_counts.head(15)).mark_bar(
                    cornerRadiusTopLeft=4,
                    cornerRadiusTopRight=4,
                    color='#8b5cf6'
                ).encode(
                    x=alt.X('Round:N', sort='-y', axis=alt.Axis(labelAngle=-45)),
                    y=alt.Y('Count:Q'),
                    tooltip=['Round', 'Count']
                ).properties(height=350)
                st.altair_chart(chart, use_container_width=True)
        
        with col_right:
            st.subheader("Most Active Teams (Home)")
            if 'home_team' in df.columns:
                team_counts = df['home_team'].value_counts().head(10).reset_index()
                team_counts.columns = ['Team', 'Home Matches']
                chart2 = alt.Chart(team_counts).mark_bar(
                    cornerRadiusTopLeft=4,
                    cornerRadiusTopRight=4
                ).encode(
                    x=alt.X('Team:N', sort='-y', axis=alt.Axis(labelAngle=-45)),
                    y=alt.Y('Home Matches:Q'),
                    color=alt.Color('Home Matches:Q', scale=alt.Scale(scheme='purples'), legend=None),
                    tooltip=['Team', 'Home Matches']
                ).properties(height=350)
                st.altair_chart(chart2, use_container_width=True)
    else:
        # Empty State
        st.markdown("""
        <div class="info-box">
        <p><b>📂 Henüz veri yüklenmedi</b><br>
        Sol menüden <b>"Upload Data"</b> sayfasına gidin ve JSON verinizi yükleyin.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div class="stat-card">
                <h2>1️⃣</h2>
                <p>Scraper'ı lokal çalıştırın</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="stat-card">
                <h2>2️⃣</h2>
                <p>JSON dosyasını yükleyin</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div class="stat-card">
                <h2>3️⃣</h2>
                <p>Analiz edin!</p>
            </div>
            """, unsafe_allow_html=True)


# ── MATCH EXPLORER ──────────────────────────────────────────
elif page == "Match Explorer":
    st.title("Match Explorer")
    
    if st.session_state.match_df is not None:
        df = st.session_state.match_df
        
        # Filters
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            if 'round' in df.columns:
                rounds = ["All"] + sorted(df['round'].dropna().unique().tolist())
                selected_round = st.selectbox("Round / Hafta", rounds)
            else:
                selected_round = "All"
        
        with col_f2:
            all_teams = set()
            if 'home_team' in df.columns:
                all_teams.update(df['home_team'].dropna().unique())
            if 'away_team' in df.columns:
                all_teams.update(df['away_team'].dropna().unique())
            teams_list = ["All"] + sorted(all_teams)
            selected_team = st.selectbox("Team Filter", teams_list)
        
        with col_f3:
            score_filter = st.selectbox("Score Status", ["All", "Played", "Not Played"])
        
        # Apply filters
        filtered = df.copy()
        if selected_round != "All" and 'round' in filtered.columns:
            filtered = filtered[filtered['round'] == selected_round]
        if selected_team != "All":
            mask = pd.Series(False, index=filtered.index)
            if 'home_team' in filtered.columns:
                mask |= (filtered['home_team'] == selected_team)
            if 'away_team' in filtered.columns:
                mask |= (filtered['away_team'] == selected_team)
            filtered = filtered[mask]
        if score_filter == "Played":
            filtered = filtered[filtered['score'] != 'vs']
        elif score_filter == "Not Played":
            filtered = filtered[filtered['score'] == 'vs']
        
        st.caption(f"Showing {len(filtered):,} of {len(df):,} matches")
        
        # Display columns
        display_cols = [c for c in ['round', 'date_str', 'home_team', 'score', 'away_team', 'venue'] if c in filtered.columns]
        
        st.dataframe(
            filtered[display_cols] if display_cols else filtered,
            column_config={
                "round": "Hafta",
                "date_str": "Tarih",
                "home_team": "Ev Sahibi",
                "score": "Skor",
                "away_team": "Deplasman",
                "venue": "Salon"
            },
            use_container_width=True,
            hide_index=True,
            height=600
        )
        
        # Download filtered data
        csv = filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Filtered Data (CSV)",
            csv,
            "filtered_matches.csv",
            "text/csv"
        )
    else:
        st.info("📂 Upload data first from the 'Upload Data' page.")


# ── TEAM ANALYSIS ───────────────────────────────────────────
elif page == "Team Analysis":
    st.title("Team Analysis")
    
    if st.session_state.match_df is not None:
        df = st.session_state.match_df
        
        # Build team stats
        all_teams = set()
        if 'home_team' in df.columns:
            all_teams.update(df['home_team'].dropna().unique())
        if 'away_team' in df.columns:
            all_teams.update(df['away_team'].dropna().unique())
        
        selected_team = st.selectbox("Select Team", sorted(all_teams))
        
        if selected_team:
            # Filter matches for this team
            home_mask = df['home_team'] == selected_team if 'home_team' in df.columns else pd.Series(False, index=df.index)
            away_mask = df['away_team'] == selected_team if 'away_team' in df.columns else pd.Series(False, index=df.index)
            team_matches = df[home_mask | away_mask]
            
            # Calculate stats
            total = len(team_matches)
            played = team_matches[team_matches['score'] != 'vs'] if 'score' in team_matches.columns else team_matches
            
            wins = 0
            losses = 0
            if 'home_sets' in played.columns and 'away_sets' in played.columns:
                for _, row in played.iterrows():
                    hs = row.get('home_sets', 0) or 0
                    as_ = row.get('away_sets', 0) or 0
                    is_home = row.get('home_team') == selected_team
                    if is_home:
                        if hs > as_:
                            wins += 1
                        elif as_ > hs:
                            losses += 1
                    else:
                        if as_ > hs:
                            wins += 1
                        elif hs > as_:
                            losses += 1
            
            # Display Stats
            st.markdown(f"### {selected_team}")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Matches", total)
            col2.metric("Played", len(played))
            col3.metric("Wins", wins, delta=f"{(wins/len(played)*100):.0f}%" if len(played) > 0 else None)
            col4.metric("Losses", losses)
            
            st.markdown("---")
            
            # Win/Loss Chart
            if wins + losses > 0:
                wl_data = pd.DataFrame({
                    'Result': ['Win', 'Loss'],
                    'Count': [wins, losses]
                })
                chart_wl = alt.Chart(wl_data).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta('Count:Q'),
                    color=alt.Color('Result:N', scale=alt.Scale(
                        domain=['Win', 'Loss'],
                        range=['#10b981', '#ef4444']
                    )),
                    tooltip=['Result', 'Count']
                ).properties(height=250, title="Win/Loss Distribution")
                st.altair_chart(chart_wl, use_container_width=True)
            
            # Match History
            st.subheader("Match History")
            display_cols = [c for c in ['round', 'date_str', 'home_team', 'score', 'away_team', 'venue'] if c in team_matches.columns]
            st.dataframe(
                team_matches[display_cols] if display_cols else team_matches,
                column_config={
                    "round": "Hafta",
                    "date_str": "Tarih",
                    "home_team": "Ev Sahibi",
                    "score": "Skor",
                    "away_team": "Deplasman",
                    "venue": "Salon"
                },
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("📂 Upload data first from the 'Upload Data' page.")


# ── UPLOAD DATA ─────────────────────────────────────────────
elif page == "Upload Data":
    st.title("Upload Data")
    
    st.markdown("""
    <div class="hero-banner">
        <h1>📂 Veri Yükleme</h1>
        <p>Lokal olarak çektiğiniz JSON verilerini buraya yükleyin ve analiz edin.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # File Upload
    uploaded_file = st.file_uploader(
        "JSON dosyası seçin",
        type=["json"],
        help="Scraper ile oluşturulmuş JSON dosyasını yükleyin"
    )
    
    if uploaded_file:
        try:
            data = json.load(uploaded_file)
            
            if isinstance(data, list):
                df = load_match_data(data)
                st.session_state.match_data = data
                st.session_state.match_df = df
                
                st.success(f"✅ {len(data):,} kayıt başarıyla yüklendi!")
                
                # Preview
                st.subheader("Data Preview")
                st.dataframe(df.head(20), use_container_width=True, hide_index=True)
                
                # Column info
                st.subheader("Columns")
                st.write(", ".join(df.columns.tolist()))
                
            elif isinstance(data, dict):
                # Single tournament detail
                st.success(f"✅ Tournament loaded: {data.get('name', 'Unknown')}")
                
                if data.get('standings'):
                    st.subheader("Standings")
                    st.dataframe(pd.DataFrame(data['standings']), use_container_width=True, hide_index=True)
                
                if data.get('teams'):
                    st.subheader("Teams")
                    st.dataframe(pd.DataFrame(data['teams']), use_container_width=True, hide_index=True)
                    
                if data.get('matches'):
                    df = load_match_data(data['matches'])
                    st.session_state.match_data = data['matches']
                    st.session_state.match_df = df
                    st.subheader("Matches")
                    st.dataframe(df, use_container_width=True, hide_index=True)
        
        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")
    
    st.markdown("---")
    
    st.subheader("💻 Lokal Scraping Komutları")
    st.code("""
# Turnuva maçlarını çekmek için:
python main.py tournament-matches "https://women.volleybox.net/tr/tournament-url"

# Takım listesi çekmek için:
python main.py teams --pages 5

# Sonuçlar JSON olarak kaydedilir, ardından buraya yükleyebilirsiniz.
""", language="bash")
