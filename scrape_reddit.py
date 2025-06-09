import praw
import pandas as pd
from datetime import datetime
import os

reddit = praw.Reddit(
    client_id=os.environ.get("REDDIT_CLIENT_ID"),
    client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
    user_agent='civil_unrest_tracker:v1.0 (by u/can_only_comment_OK)'
)

subreddits = ['news', 'politics', 'nyc', 'Portland', 'LosAngeles', 'Chicago', 'Seattle', 'BlackLivesMatter']
keywords = ['protest', 'riot', 'looting', 'march', 'police', 'shooting', 'tear gas', 'antifa']

results = []

for sub in subreddits:
    for submission in reddit.subreddit(sub).new(limit=100):
        text = (submission.title or '') + " " + (submission.selftext or '')
        if any(word in text.lower() for word in keywords):
            results.append({
                'platform': 'reddit',
                'text': text,
                'author': submission.author.name if submission.author else 'unknown',
                'date': datetime.utcfromtimestamp(submission.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                'url': submission.url,
                'source_subreddit': sub
            })

df = pd.DataFrame(results)
df.to_csv('data/raw/reddit_signals.csv', index=False)
print(f"Scraped {len(results)} Reddit posts.")
