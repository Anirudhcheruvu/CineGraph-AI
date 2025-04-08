import pandas as pd
from collections import Counter

df = pd.read_csv("imdb_top_1000.csv")
genre_list = df["Genre"].tolist()

all_genres = []
for entry in genre_list:
    if pd.isnull(entry):
        continue
    # Remove extra quotes if present
    cleaned_entry = entry.replace('"', '')
    # Split the genres by comma and strip extra whitespace
    genres = [g.strip().lower() for g in cleaned_entry.split(',')]
    all_genres.extend(genres)

# Get the frequency of each individual genre
genre_counts = Counter(all_genres)
print("Genre frequencies:", genre_counts)

# Identify potential problematic data points (e.g., very rare genres)
for genre, count in genre_counts.items():
    if count < 10:  # adjust threshold as needed
        print(f"Potential problematic genre: '{genre}' appears {count} times")
