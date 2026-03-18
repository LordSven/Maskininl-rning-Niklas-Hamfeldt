import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
tags = pd.read_csv(r'ml-latest\tags.csv')
ratings = pd.read_csv(r'ml-latest\ratings.csv')
movies = pd.read_csv(r'ml-latest\movies.csv')
links = pd.read_csv(r'ml-latest\links.csv')

movies['genres'] = movies['genres'].str.replace('|', ' ', regex=False)

tags = tags.groupby('movieId')['tag'].agg(lambda x: ' '.join(x.dropna().astype(str))).reset_index()

movies = movies.merge(tags, 'left')

movies = movies.fillna('')

movies['genres+tags'] = movies['genres'] + ' ' + movies['tag']

vectorizer = TfidfVectorizer()
genres_vector = vectorizer.fit_transform(movies['genres'])
tags_vector = vectorizer.fit_transform(movies['tag'])
combined_vector = vectorizer.fit_transform(movies['genres+tags'])

def recommend():
    movie = input('Ange titel eller sökord för vilken film vill du har rekommendationer baserat på: ')

    words = movie.lower().split()
    mask = pd.Series([all(word in title.lower() for word in words) for title in movies['title']])
    alternatives = movies[mask]
    while alternatives.empty:
        movie = input('Inga filmer hittades, försök igen: ')
        words = movie.lower().split()
        mask = pd.Series([all(word in title.lower() for word in words) for title in movies['title']])
        alternatives = movies[mask]
    for i, title in enumerate(alternatives['title']):
        print(f'{i}: {title}')

    
    choice = input('Här är filmerna som matchar titeln du gav, ange siffran för den filmen du tänkte på: ')
    choice_index = alternatives.iloc[int(choice)].name
    choice_vector = combined_vector[int(choice_index)]

    X = combined_vector
    Y = choice_vector

    similarity = cosine_similarity(X, Y).flatten()
    sorted_indices = np.argsort(similarity)

    rec_movies = sorted_indices[-6:-1]

    print(f'Rekommendationerna baserat på {alternatives.iloc[int(choice)]['title']} är:')
    for title in movies['title'].loc[rec_movies].values:
        print(title)

    return

recommend()