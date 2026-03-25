import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import hstack

tags = pd.read_csv(r'ml-latest\tags.csv')
ratings = pd.read_csv(r'ml-latest\ratings.csv')
movies = pd.read_csv(r'ml-latest\movies.csv')
links = pd.read_csv(r'ml-latest\links.csv')

movies['title'] = movies['title'].str.replace(r'^(.*),\s(The|A|An)\s(\(\d{4}\))$', r'\2 \1 \3', regex=True)

mean_ratings = ratings.groupby('movieId')['rating'].mean().reset_index()

tags = tags.groupby('movieId')['tag'].agg(lambda x: ' '.join(x.dropna().astype(str))).reset_index()

movies['genres'] = movies['genres'].str.replace('|', ' ', regex=False)
movies = movies.merge(tags, 'left', 'movieId')
movies = movies.fillna('')
movies['year'] = movies['title'].str.extract(r'\((\d{4})\)')
movies = movies.merge(mean_ratings, 'left', 'movieId')
movies['genres+tags'] = movies['genres'] + ' ' + movies['tag']
movies = movies.dropna().reset_index(drop=True)

genres_vectorizer = TfidfVectorizer()
tags_vectorizer = TfidfVectorizer(min_df=2, max_df=0.9)
genres_vector = genres_vectorizer.fit_transform(movies['genres'])
tags_vector = tags_vectorizer.fit_transform(movies['tag'])
combined_vector = hstack([genres_vector, tags_vector * 1.5])

def recommend():
    try:
        n = int(input('Hur många filmer vill du basera rekommendationerna på? (1-3): '))
    except ValueError:
        n = 0
    while n < 1 or n > 3:
        try:
            n = int(input('Du måste välja en siffra mellan 1-3: '))
        except ValueError:
            n = 0
    vectors = []
    years = []
    titles = []
    chosen_indices = []
    rankings = []
    
    for i in range(n):
        movie = input(f'Ange titel eller sökord för film #{i+1}: ')

        words = movie.lower().split()
        mask = pd.Series([all(word in title.lower() for word in words) for title in movies['title']])
        alternatives = movies[mask]
        while alternatives.empty:
            movie = input('Inga filmer hittades, försök igen: ')
            words = movie.lower().split()
            mask = pd.Series([all(word in title.lower() for word in words) for title in movies['title']])
            alternatives = movies[mask]
        for j, title in enumerate(alternatives['title']):
            print(f'{j}: {title}')

        choice = input('Här är filmerna som matchar titeln du gav, ange siffran för den filmen du tänkte på: ')

        years.append(alternatives.iloc[int(choice)]['year'])
        titles.append(alternatives.iloc[int(choice)]['title'])
        vectors.append(combined_vector[alternatives.iloc[int(choice)].name])
        chosen_indices.append(alternatives.iloc[int(choice)].name)
        
        similarity = cosine_similarity(combined_vector, vectors[-1]).flatten()
        rankings.append(np.argsort(np.argsort(similarity)))
    
    combined_rankings = sum(rankings)

    year_min = min(float(y) for y in years) - 10
    year_max = max(float(y) for y in years) + 10

    top50 = [i for i in np.argsort(combined_rankings)[-54:] if i not in chosen_indices][-50:]

    year_filtered = movies.loc[top50]
    year_filtered = year_filtered[pd.to_numeric(year_filtered['year'], errors='coerce').between(year_min, year_max)]

    rec_movies = year_filtered.sort_values(by='rating', ascending=False).head(5).index

    print(f'Rekommendationerna baserat på {', '.join(titles)} är:')
    for title in movies['title'].loc[rec_movies].values:
        print(title)

    return

recommend()