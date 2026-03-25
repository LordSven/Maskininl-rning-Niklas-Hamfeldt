import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import hstack

tags = pd.read_csv(r'ml-latest\tags.csv')
ratings = pd.read_csv(r'ml-latest\ratings.csv')
movies = pd.read_csv(r'ml-latest\movies.csv')
links = pd.read_csv(r'ml-latest\links.csv')

mean_ratings = ratings.groupby('movieId')['rating'].mean().reset_index()
tags = tags.groupby('movieId')['tag'].agg(lambda x: ' '.join(x.dropna().astype(str))).reset_index()

movies['title'] = movies['title'].str.replace(r'^(.*),\s(The|A|An)\s(\(\d{4}\))$', r'\2 \1 \3', regex=True)
movies['genres'] = movies['genres'].str.replace('|', ' ', regex=False)
movies = movies.merge(tags, 'left', 'movieId')
movies = movies.fillna('')
movies['year'] = movies['title'].str.extract(r'\((\d{4})\)')
movies = movies.merge(mean_ratings, 'left', 'movieId')
movies = movies.merge(links[['movieId', 'imdbId']], on='movieId', how='left')
movies['genres+tags'] = movies['genres'] + ' ' + movies['tag']
movies = movies.dropna().reset_index(drop=True)

genres_vectorizer = TfidfVectorizer()
tags_vectorizer = TfidfVectorizer(min_df=2, max_df=0.9)
genres_vector = genres_vectorizer.fit_transform(movies['genres'])
tags_vector = tags_vectorizer.fit_transform(movies['tag'])
combined_vector = hstack([genres_vector, tags_vector * 1.5])

def search_movies(query):
    words = query.lower().split()
    mask = pd.Series([all(word in title.lower() for word in words) for title in movies['title']])
    return movies[mask][['title']].reset_index()

def get_movie_info(movie_index):
    row = movies.iloc[movie_index]
    return {'title': row['title'], 'rating': row['rating']}

def get_rankings(movie_index):
    vector = combined_vector[movie_index]
    similarity = cosine_similarity(combined_vector, vector).flatten()
    return np.argsort(np.argsort(similarity))

def get_recommendations(chosen_indices, rankings, years):
    if not chosen_indices:
        return []

    combined_rankings = sum(rankings)
    year_min = min(float(y) for y in years) - 10
    year_max = max(float(y) for y in years) + 10

    top50 = [i for i in np.argsort(combined_rankings)[-53:] if i not in chosen_indices][-50:]
    year_filtered = movies.loc[top50]
    year_filtered = year_filtered[pd.to_numeric(year_filtered['year'], errors='coerce').between(year_min, year_max)]

    return year_filtered.index