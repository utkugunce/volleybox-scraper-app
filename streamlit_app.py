import streamlit as st
import pandas as pd
import altair as alt
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.core import VolleyboxScraper
from scraper.teams import scrape_team_list, scrape_team_profile
from scraper.tournaments import scrape_tournament_detail, scrape_tournament_matches

# Page config
st.set_page_config(
    page_title="Volleybox Scraper",
    page_icon="🏐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
.stApp { background-color: #0f172a; font-family: 'Inter', sans-serif; }
h1,h2,h3,h4 { color: #f8fafc !important; font-family: 'Inter', sans-serif !important; font-weight: 600 !important; }

div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    padding: 1.2rem; border-radius: 0.75rem;
    border: 1px solid rgba(148,163,184,0.12);
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.15);
}
div[data-testid="stMetric"] label { color: #94a3b8 !important; font-size: 0.85rem !important; }
div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #f8fafc !important; font-weight: 700 !important; }

.stButton>button {
    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
    color: white; border: none; border-radius: 0.5rem;
    font-weight: 600; padding: 0.6rem 1.5rem;
    transition: all 0.3s ease;
    box-shadow: 0 2px 8px rgba(139,92,246,0.3);
}
.stButton>button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(139,92,246,0.5); }

section[data-testid="stSidebar"] { background-color: #020617; border-right: 1px solid rgba(148,163,184,0.12); }

.hero-banner {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4c1d95 100%);
    padding: 2rem 2.5rem; border-radius: 1rem; margin-bottom: 1.5rem;
    border: 1px solid rgba(139,92,246,0.2);
}
.hero-banner h1 { margin: 0; font-size: 2rem; }
.hero-banner p { color: #c4b5fd !important; margin-top: 0.5rem; font-size: 1.05rem; }
</style>
""", unsafe_allow_html=True)

# ── Session State ───────────────────────────────────────────
if 'scraper' not in st.session_state:
    st.session_state.scraper = None

def get_scraper():
    if st.session_state.scraper is None:
        st.session_state.scraper = VolleyboxScraper(headless=True)
    return st.session_state.scraper

def load_match_data(data):
    df = pd.DataFrame(data)
    if 'score' in df.columns:
        df['score'] = df['score'].fillna('vs')
    if 'date_str' in df.columns:
        df['date_str'] = df['date_str'].fillna('')
    if 'home_sets' in df.columns and 'away_sets' in df.columns:
        df['home_sets'] = pd.to_numeric(df['home_sets'], errors='coerce')
        df['away_sets'] = pd.to_numeric(df['away_sets'], errors='coerce')
    return df

# ── Sidebar ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🏐 Volleybox")
    st.caption("Live Scraper Dashboard")
    
    page = st.radio(
        "Navigation",
        ["🏆 Turnuva Çek", "👥 Takım Çek", "📊 Maç Analizi", "📋 Takım Analizi"]
    )
    
    st.divider()
    if st.button("🔄 Scraper Yenile"):
        if st.session_state.scraper:
            st.session_state.scraper.close()
        st.session_state.scraper = None
        st.success("Scraper sıfırlandı!")


# ── TURNUVA ÇEK ────────────────────────────────────────────
if page == "🏆 Turnuva Çek":
    st.markdown("""
    <div class="hero-banner">
        <h1>🏆 Turnuva Verisi Çek</h1>
        <p>Turnuva URL'sini yapıştırın, detaylar ve maçlar anında çekilsin.</p>
    </div>
    """, unsafe_allow_html=True)
    
    tourney_url = st.text_input(
        "Turnuva URL'si",
        placeholder="https://women.volleybox.net/tr/women-turkiye-kadnlar-voleybol-2-ligi-2025-26-o38677"
    )
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        scrape_detail = st.button("📋 Detay & Puan Durumu", type="primary")
    with col_btn2:
        scrape_matches = st.button("⚽ Tüm Maçları Çek")
    
    # --- DETAY ---
    if scrape_detail and tourney_url:
        progress = st.progress(0, text="Bağlanıyor...")
        result_area = st.empty()
        
        try:
            scraper = get_scraper()
            progress.progress(0.3, text="Tarayıcı hazır, sayfa yükleniyor...")
            
            detail = scrape_tournament_detail(scraper, tourney_url)
            progress.progress(0.8, text="Veriler çıkarılıyor...")
            
            if detail:
                progress.progress(1.0, text="✅ Tamamlandı!")
                st.session_state.tournament_detail = detail
                
                st.success(f"**{detail.get('name', 'N/A')}**")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Sezon", detail.get('season', 'N/A'))
                col2.metric("Takım", detail.get('team_count', len(detail.get('teams', []))))
                col3.metric("Ülke", detail.get('country', 'N/A'))
                
                if detail.get('standings'):
                    st.subheader("Puan Durumu")
                    st.dataframe(pd.DataFrame(detail['standings']), use_container_width=True, hide_index=True)
                
                if detail.get('teams'):
                    st.subheader("Takımlar")
                    st.dataframe(pd.DataFrame(detail['teams']), use_container_width=True, hide_index=True)
                
                if detail.get('matches'):
                    st.subheader("Maçlar")
                    st.dataframe(pd.DataFrame(detail['matches']), use_container_width=True, hide_index=True)
                
                json_str = json.dumps(detail, ensure_ascii=False, indent=2)
                st.download_button("📥 JSON İndir", json_str, "tournament_detail.json", "application/json")
            else:
                progress.progress(1.0, text="❌ Veri çekilemedi")
        except Exception as e:
            st.error(f"Hata: {str(e)}")
    
    # --- TÜM MAÇLAR ---
    if scrape_matches and tourney_url:
        matches_url = tourney_url
        if not matches_url.endswith('/matches'):
            matches_url = matches_url.rstrip('/') + '/matches'
        
        progress_bar = st.progress(0, text="Hazırlanıyor...")
        status_text = st.empty()
        match_counter = st.empty()
        
        def on_progress(round_idx, round_total, match_count, round_name):
            pct = round_idx / max(round_total, 1)
            progress_bar.progress(pct, text=f"Tur {round_idx}/{round_total}: {round_name}")
            match_counter.metric("Çekilen Maç", f"{match_count:,}")
        
        try:
            scraper = get_scraper()
            status_text.info("Tarayıcı hazır, maçlar yükleniyor...")
            
            matches = scrape_tournament_matches(scraper, matches_url, progress_callback=on_progress)
            
            progress_bar.progress(1.0, text="Tamamlandı!")
            status_text.empty()
            
            if matches:
                match_counter.metric("Toplam Çekilen Maç", f"{len(matches):,}")
                
                df_matches = load_match_data(matches)
                st.session_state.match_data = matches
                st.session_state.match_df = df_matches
                
                st.success(f"**{len(matches)} maç** yüklendi! 📊 Maç Analizi sayfasından detaylı analiz yapabilirsiniz.")
                
                display_cols = [c for c in ['round', 'date_str', 'home_team', 'score', 'away_team', 'venue'] if c in df_matches.columns]
                st.dataframe(
                    df_matches[display_cols] if display_cols else df_matches,
                    use_container_width=True, hide_index=True, height=400
                )
                
                json_str = json.dumps(matches, ensure_ascii=False, indent=2)
                st.download_button("📥 Maçları JSON İndir", json_str, "tournament_matches.json", "application/json")
            else:
                st.error("❌ Maç bulunamadı")
        except Exception as e:
            st.error(f"Hata: {str(e)}")


# ── TAKIM ÇEK ──────────────────────────────────────────────
elif page == "👥 Takım Çek":
    st.markdown("""
    <div class="hero-banner">
        <h1>👥 Takım Detayı Çek</h1>
        <p>Takım URL'sini yapıştırın, kadro ve bilgiler anında çekilsin.</p>
    </div>
    """, unsafe_allow_html=True)
    
    team_url = st.text_input(
        "Takım URL'si",
        placeholder="https://women.volleybox.net/tr/team-name-t12345"
    )
    
    if st.button("🔍 Takım Bilgilerini Çek", type="primary") and team_url:
        progress = st.progress(0, text="Bağlanıyor...")
        
        try:
            scraper = get_scraper()
            progress.progress(0.3, text="Tarayıcı hazır, takım sayfası yükleniyor...")
            
            detail = scrape_team_profile(scraper, team_url)
            progress.progress(0.8, text="Veriler çıkarılıyor...")
            
            if detail:
                progress.progress(1.0, text="✅ Tamamlandı!")
                st.success(f"**{detail.get('name', 'N/A')}**")
                st.caption(f"{detail.get('country', '')} • {detail.get('league', '')}")
                
                if detail.get('roster'):
                    st.subheader("Kadro")
                    df_r = pd.DataFrame(detail['roster'])
                    st.dataframe(df_r, use_container_width=True, hide_index=True)
                    
                    if 'height' in df_r.columns and 'position' in df_r.columns:
                        df_r['height_num'] = pd.to_numeric(df_r['height'].astype(str).str.replace('cm', ''), errors='coerce')
                        
                        col_c1, col_c2 = st.columns(2)
                        with col_c1:
                            chart = alt.Chart(df_r.dropna(subset=['height_num'])).mark_bar(
                                cornerRadiusTopLeft=4, cornerRadiusTopRight=4
                            ).encode(
                                x=alt.X('player_name:N', sort='-y', title='Oyuncu'),
                                y=alt.Y('height_num:Q', title='Boy (cm)'),
                                color=alt.Color('position:N', legend=None),
                                tooltip=['player_name', 'height_num', 'position']
                            ).properties(title="Oyuncu Boyları", height=300)
                            st.altair_chart(chart, use_container_width=True)
                        
                        with col_c2:
                            chart_pos = alt.Chart(df_r).mark_arc(innerRadius=50).encode(
                                theta=alt.Theta("count()", stack=True),
                                color=alt.Color("position:N"),
                                tooltip=["position", "count()"]
                            ).properties(title="Pozisyon Dağılımı", height=300)
                            st.altair_chart(chart_pos, use_container_width=True)
                
                json_str = json.dumps(detail, ensure_ascii=False, indent=2)
                st.download_button("📥 JSON İndir", json_str, "team_detail.json", "application/json")
            else:
                progress.progress(1.0, text="❌ Veri çekilemedi")
        except Exception as e:
            st.error(f"Hata: {str(e)}")


# ── MAÇ ANALİZİ ────────────────────────────────────────────
elif page == "📊 Maç Analizi":
    st.title("Maç Analizi")
    
    if 'match_df' not in st.session_state or st.session_state.get('match_df') is None:
        st.info("Önce 🏆 Turnuva Çek sayfasından maç verisi çekin.")
    else:
        df = st.session_state.match_df
        
        # Summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Toplam Maç", f"{len(df):,}")
        with col2:
            teams = set()
            if 'home_team' in df.columns: teams.update(df['home_team'].dropna().unique())
            if 'away_team' in df.columns: teams.update(df['away_team'].dropna().unique())
            st.metric("Takım", f"{len(teams):,}")
        with col3:
            st.metric("Hafta", f"{df['round'].nunique():,}" if 'round' in df.columns else "N/A")
        with col4:
            st.metric("Salon", f"{df['venue'].nunique():,}" if 'venue' in df.columns else "N/A")
        
        st.markdown("---")
        
        # Filters
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            rounds = ["Tümü"] + sorted(df['round'].dropna().unique().tolist()) if 'round' in df.columns else ["Tümü"]
            selected_round = st.selectbox("Hafta", rounds)
        with col_f2:
            all_teams = set()
            if 'home_team' in df.columns: all_teams.update(df['home_team'].dropna().unique())
            if 'away_team' in df.columns: all_teams.update(df['away_team'].dropna().unique())
            selected_team = st.selectbox("Takım", ["Tümü"] + sorted(all_teams))
        with col_f3:
            score_filter = st.selectbox("Durum", ["Tümü", "Oynandı", "Oynanmadı"])
        
        filtered = df.copy()
        if selected_round != "Tümü" and 'round' in filtered.columns:
            filtered = filtered[filtered['round'] == selected_round]
        if selected_team != "Tümü":
            mask = pd.Series(False, index=filtered.index)
            if 'home_team' in filtered.columns: mask |= (filtered['home_team'] == selected_team)
            if 'away_team' in filtered.columns: mask |= (filtered['away_team'] == selected_team)
            filtered = filtered[mask]
        if score_filter == "Oynandı":
            filtered = filtered[filtered['score'] != 'vs']
        elif score_filter == "Oynanmadı":
            filtered = filtered[filtered['score'] == 'vs']
        
        st.caption(f"{len(filtered):,} / {len(df):,} maç gösteriliyor")
        
        display_cols = [c for c in ['round', 'date_str', 'home_team', 'score', 'away_team', 'venue'] if c in filtered.columns]
        st.dataframe(
            filtered[display_cols] if display_cols else filtered,
            column_config={"round": "Hafta", "date_str": "Tarih", "home_team": "Ev Sahibi", "score": "Skor", "away_team": "Deplasman", "venue": "Salon"},
            use_container_width=True, hide_index=True, height=500
        )
        
        csv = filtered.to_csv(index=False).encode('utf-8')
        st.download_button("📥 CSV İndir", csv, "maclar.csv", "text/csv")
        
        # Charts
        st.markdown("---")
        col_left, col_right = st.columns(2)
        with col_left:
            if 'round' in df.columns:
                st.subheader("Haftalık Maç Sayısı")
                rc = df['round'].value_counts().reset_index()
                rc.columns = ['Hafta', 'Maç']
                chart = alt.Chart(rc.head(15)).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color='#8b5cf6').encode(
                    x=alt.X('Hafta:N', sort='-y'), y='Maç:Q', tooltip=['Hafta', 'Maç']
                ).properties(height=300)
                st.altair_chart(chart, use_container_width=True)
        with col_right:
            if 'home_team' in df.columns:
                st.subheader("En Çok Ev Sahibi Olan Takımlar")
                tc = df['home_team'].value_counts().head(10).reset_index()
                tc.columns = ['Takım', 'Maç']
                chart2 = alt.Chart(tc).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                    x=alt.X('Takım:N', sort='-y'), y='Maç:Q',
                    color=alt.Color('Maç:Q', scale=alt.Scale(scheme='purples'), legend=None),
                    tooltip=['Takım', 'Maç']
                ).properties(height=300)
                st.altair_chart(chart2, use_container_width=True)


# ── TAKIM ANALİZİ ──────────────────────────────────────────
elif page == "📋 Takım Analizi":
    st.title("Takım Analizi")
    
    if 'match_df' not in st.session_state or st.session_state.get('match_df') is None:
        st.info("Önce 🏆 Turnuva Çek sayfasından maç verisi çekin.")
    else:
        df = st.session_state.match_df
        all_teams = set()
        if 'home_team' in df.columns: all_teams.update(df['home_team'].dropna().unique())
        if 'away_team' in df.columns: all_teams.update(df['away_team'].dropna().unique())
        
        selected_team = st.selectbox("Takım Seç", sorted(all_teams))
        
        if selected_team:
            home_mask = df['home_team'] == selected_team if 'home_team' in df.columns else pd.Series(False, index=df.index)
            away_mask = df['away_team'] == selected_team if 'away_team' in df.columns else pd.Series(False, index=df.index)
            team_matches = df[home_mask | away_mask]
            played = team_matches[team_matches['score'] != 'vs'] if 'score' in team_matches.columns else team_matches
            
            wins = losses = 0
            if 'home_sets' in played.columns and 'away_sets' in played.columns:
                for _, row in played.iterrows():
                    hs = row.get('home_sets', 0) or 0
                    as_ = row.get('away_sets', 0) or 0
                    is_home = row.get('home_team') == selected_team
                    if is_home:
                        wins += 1 if hs > as_ else 0
                        losses += 1 if as_ > hs else 0
                    else:
                        wins += 1 if as_ > hs else 0
                        losses += 1 if hs > as_ else 0
            
            st.markdown(f"### {selected_team}")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Toplam", len(team_matches))
            col2.metric("Oynanan", len(played))
            col3.metric("Galibiyet", wins, delta=f"{(wins/len(played)*100):.0f}%" if len(played)>0 else None)
            col4.metric("Mağlubiyet", losses)
            
            if wins + losses > 0:
                wl = pd.DataFrame({'Sonuç': ['Galibiyet', 'Mağlubiyet'], 'Sayı': [wins, losses]})
                chart_wl = alt.Chart(wl).mark_arc(innerRadius=50).encode(
                    theta='Sayı:Q',
                    color=alt.Color('Sonuç:N', scale=alt.Scale(domain=['Galibiyet','Mağlubiyet'], range=['#10b981','#ef4444'])),
                    tooltip=['Sonuç', 'Sayı']
                ).properties(height=250)
                st.altair_chart(chart_wl, use_container_width=True)
            
            st.subheader("Maç Geçmişi")
            display_cols = [c for c in ['round', 'date_str', 'home_team', 'score', 'away_team', 'venue'] if c in team_matches.columns]
            st.dataframe(
                team_matches[display_cols] if display_cols else team_matches,
                column_config={"round": "Hafta", "date_str": "Tarih", "home_team": "Ev Sahibi", "score": "Skor", "away_team": "Deplasman", "venue": "Salon"},
                use_container_width=True, hide_index=True
            )
