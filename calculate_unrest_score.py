import pandas as pd
from datetime import datetime, timedelta
import argparse
import os

# Argument parser for CLI use
parser = argparse.ArgumentParser(description="Calculate unrest scores by time window")
parser.add_argument("--hours", type=int, default=24, help="How many hours back to consider (e.g. 24, 48, 168)")
args = parser.parse_args()

# Load processed signals
reddit = pd.read_csv("data/processed/reddit_with_locations.csv")
news = pd.read_csv("data/processed/news_with_locations.csv")
df = pd.concat([reddit, news], ignore_index=True)

# Preprocessing
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df = df.dropna(subset=['city', 'date'])

# Filter by time
cutoff = datetime.utcnow() - timedelta(hours=args.hours)
df = df[df['date'] >= cutoff]

# Scoring config
platform_weights = {'reddit': 1, 'news': 3}
keyword_weights = {
    'riot': 5, 'looting': 4, 'shooting': 4,
    'tear gas': 3, 'march': 2, 'protest': 2, 'police': 1
}

def get_keyword_score(text):
    text = str(text).lower()
    return sum(weight for keyword, weight in keyword_weights.items() if keyword in text)

def get_time_weight(post_time):
    hours_ago = (datetime.utcnow() - post_time).total_seconds() / 3600
    if hours_ago <= 24:
        return 1.0
    elif hours_ago <= 48:
        return 0.5
    else:
        return 0.2

scores = {}

for _, row in df.iterrows():
    city = row['city']
    base_score = platform_weights.get(row['platform'], 1)
    keyword_score = get_keyword_score(row['text'])
    time_decay = get_time_weight(row['date'])
    confidence = row.get('confidence', 0.3)

    signal_score = (base_score + keyword_score) * time_decay * confidence

    if city not in scores:
        scores[city] = {
            'total_score': 0,
            'state': row['state'],
            'lat': row['lat'],
            'lon': row['lon'],
            'count': 0
        }

    scores[city]['total_score'] += signal_score
    scores[city]['count'] += 1

# Format output
result_df = pd.DataFrame([
    {
        'city': city,
        'state': data['state'],
        'lat': data['lat'],
        'lon': data['lon'],
        'signal_count': data['count'],
        'unrest_score': round(data['total_score'], 2)
    }
    for city, data in scores.items()
])

# Sort and save
result_df.sort_values(by='unrest_score', ascending=False, inplace=True)
output_path = f"data/final/unrest_scores_{args.hours}h.csv"
os.makedirs("data/final/", exist_ok=True)
result_df.to_csv(output_path, index=False)

print(f"✅ Saved {len(result_df)} scores to {output_path}")
