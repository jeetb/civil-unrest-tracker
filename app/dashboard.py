import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import os

# Setup
st.set_page_config(page_title="U.S. Civil Unrest Tracker", layout="wide")
st.title("🗺️ U.S. Civil Unrest Tracker (MVP)")

# Sidebar filters
min_score = st.sidebar.slider("Minimum unrest score", 0, 100, 20)
max_results = st.sidebar.slider("Max cities to show", 10, 100, 50)
time_window = st.sidebar.selectbox("Time window", ["Last 24h", "Last 48h", "Last 7 days"])
hours_lookup = {"Last 24h": 24, "Last 48h": 48, "Last 7 days": 168}
hours_selected = hours_lookup[time_window]
cutoff = datetime.utcnow() - timedelta(hours=hours_selected)

# Determine which score file to load
score_file = f"../data/final/unrest_scores_{hours_selected}h.csv"
if not os.path.exists(score_file):
    st.error(f"⚠️ Score file not found: {score_file}\nPlease generate it locally and re-upload to the repo.")
    st.stop()

if not os.path.exists(score_file):
    st.error(f"⚠️ Score file not found for {hours_selected}h window: `{score_file}`.\n\nPlease run:\n`python calculate_unrest_score.py --hours {hours_selected}`")
    st.stop()

# Load the appropriate score file
score_df = pd.read_csv(score_file).dropna(subset=['lat', 'lon'])

# Load raw signals and filter by time
reddit = pd.read_csv("../data/processed/reddit_with_locations.csv")
news = pd.read_csv("../data/processed/news_with_locations.csv")
signals = pd.concat([reddit, news], ignore_index=True)
signals['date'] = pd.to_datetime(signals['date'], errors='coerce')
signals['text'] = signals['text'].fillna('')
filtered_signals = signals[signals['date'] >= cutoff]


# Filter cities by score
filtered_scores = score_df[score_df['unrest_score'] >= min_score].head(max_results)

# Draw map
m = folium.Map(location=[39.5, -98.35], zoom_start=4, tiles="cartodbpositron")
for _, row in filtered_scores.iterrows():
    folium.CircleMarker(
        location=(row['lat'], row['lon']),
        radius=min(10, row['unrest_score'] / 10 + 3),
        popup=f"{row['city']}, {row['state']} — Score: {row['unrest_score']}",
        tooltip=f"{row['city']}, {row['state']}",
        color="red" if row['unrest_score'] > 50 else "orange",
        fill=True,
        fill_opacity=0.7
    ).add_to(m)

st_folium(m, width=1100, height=650)

# Show city breakdowns
st.subheader("🧠 Unrest Scoring Breakdown")
for _, city_row in filtered_scores.iterrows():
    city = city_row['city']
    st.markdown(f"### {city}, {city_row['state']} — Score: {city_row['unrest_score']}")

    with st.expander("📊 View Scoring Details & Sample Signals"):
        city_signals = filtered_signals[filtered_signals['city'] == city].sort_values(by='date', ascending=False).head(10)
        platform_counts = city_signals['platform'].value_counts().to_dict()
        avg_confidence = round(city_signals['confidence'].mean(), 2) if not city_signals.empty else 0.0

        st.markdown(f"- **Signals counted:** {city_row['signal_count']}")
        st.markdown(f"- **Avg. location confidence:** {avg_confidence}")
        st.markdown(f"- **By platform:** {platform_counts}")

        st.markdown("**🔍 Sample Signals:**")
        for _, sig in city_signals.iterrows():
            text = str(sig.get('text', ''))
            st.markdown(f"""
            > *{text[:200]}...*  
            > • Platform: `{sig['platform']}` | Confidence: `{sig['confidence']}`  
            > • [Link]({sig['url']}) | Date: `{sig['date']}`  
            """)



st.markdown("---")
st.markdown("*Scores reflect recent unrest signals, weighted by platform, recency, and language intensity. Not a predictive model — reflects live public discourse.*")
