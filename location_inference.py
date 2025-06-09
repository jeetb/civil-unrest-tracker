import pandas as pd
from geotext import GeoText
import spacy

# Load spaCy NER
nlp = spacy.load("en_core_web_sm")

# Load geo database
geo_df = pd.read_csv("data/geo/uscities.csv")  # Adjust path if needed
geo_df['city_lower'] = geo_df['city'].str.lower()

# Define fallback subreddit-to-location mapping
subreddit_map = {
    'nyc': ('New York', 'NY'),
    'Portland': ('Portland', 'OR'),
    'LosAngeles': ('Los Angeles', 'CA'),
    'Chicago': ('Chicago', 'IL'),
    'Seattle': ('Seattle', 'WA'),
}

def extract_city(text):
    # Extract with GeoText
    places = GeoText(text)
    geo_city = next(iter(places.cities), None)

    # Extract with spaCy
    doc = nlp(text)
    spacy_city = next((ent.text for ent in doc.ents if ent.label_ == "GPE"), None)

    return geo_city or spacy_city or None

def match_city_to_coords(city_name):
    if not city_name:
        return None

    match = geo_df[geo_df['city_lower'] == city_name.lower()]
    if not match.empty:
        row = match.iloc[0]
        return {
            'city': row['city'],
            'state': row['state_id'],
            'lat': row['lat'],
            'lon': row['lng'],
            'county': row['county_name'],
            'confidence': 0.9
        }
    return None

def fallback_from_subreddit(subreddit):
    if subreddit in subreddit_map:
        city, state = subreddit_map[subreddit]
        return match_city_to_coords(city) | {'confidence': 0.7}
    return None

def process_file(input_file, output_file, platform):
    df = pd.read_csv(input_file)
    results = []

    for _, row in df.iterrows():
        text = row['text'] if platform == 'reddit' else row.get('title', '') + ' ' + row.get('summary', '')
        location_data = match_city_to_coords(extract_city(text))

        if not location_data and platform == 'reddit':
            location_data = fallback_from_subreddit(row.get('source_subreddit'))

        row_data = row.to_dict()
        if location_data:
            row_data.update(location_data)
        else:
            row_data.update({
                'city': None, 'state': None, 'lat': None, 'lon': None, 'county': None, 'confidence': 0.3
            })

        results.append(row_data)

    result_df = pd.DataFrame(results)
    result_df.to_csv(output_file, index=False)
    print(f"Processed {len(result_df)} rows → {output_file}")

# Process both Reddit and News CSVs
process_file('data/raw/reddit_signals.csv', 'data/processed/reddit_with_locations.csv', 'reddit')
process_file('data/raw/news_signals.csv', 'data/processed/news_with_locations.csv', 'news')
