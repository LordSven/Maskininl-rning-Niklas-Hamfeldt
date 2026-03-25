from dash import Dash, html, dcc, Input, Output, State, ALL
import dash_bootstrap_components as dbc
from recommender import search_movies, get_rankings, get_recommendations, movies

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server

app.layout = html.Div(
    style={
        'backgroundColor': '#000000',
        'color': '#ffffff',
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'minHeight': '100vh',
        'paddingTop': '30px'
    },
    children=[
        html.Img(
            src='/assets/recflix.png',
            style={'width': '250px', 'marginBottom': '20px'}
        ),

        html.Div([
            html.Label('Hur många filmer vill du basera rekommendationerna på? (1-3)'),
            dcc.Input(
                id='num-movies',
                type='number',
                min=1,
                max=3,
                value=1,
                style={
                    'width': '60px',
                    'textAlign': 'center',
                    'marginLeft': '10px',
                    'backgroundColor': '#ffffff',
                    'color': '#000000',
                    'borderRadius': '4px',
                    'border': '1px solid #ccc'
                }
            ),
            html.Button('Bekräfta antal', id='confirm-num', n_clicks=0, style={'marginLeft': '10px'})
        ], style={'marginBottom': '20px'}),

        html.Div(id='movie-inputs', style={'marginBottom': '20px', 'width': '50%'}),

        html.Label('Välj sortering av rekommendationer:'),
        dcc.Dropdown(
            id='rating-choice',
            options=[
                {'label': 'Högst rating', 'value': 'high'},
                {'label': 'Lägst rating', 'value': 'low'},
                {'label': 'Närmast medelvärdet av valda filmer', 'value': 'closest'}
            ],
            value='high',
            clearable=False,
            style={
                'width': '300px',
                'backgroundColor': '#ffffff',
                'color': '#000000',
                'borderRadius': '4px',
                'border': '1px solid #ccc',
                'padding': '5px',
                'marginTop': '5px'
            }
        ),

        html.Button('Få rekommendationer', id='rec-btn', n_clicks=0, style={'marginTop':'20px', 'marginBottom': '20px'}),

        html.Div(id='recommendations', style={'fontWeight': 'bold', 'width': '60%', 'textAlign': 'center'})
    ]
)

@app.callback(
    Output('movie-inputs', 'children'),
    Input('confirm-num', 'n_clicks'),
    State('num-movies', 'value')
)
def create_movie_inputs(n_clicks, num):
    if not num or num < 1 or num > 3:
        return html.Div('Välj ett tal mellan 1 och 3', style={'color':'#ff0000'})
    
    children = []
    for i in range(num):
        children.append(
            html.Div(
                style={
                    'display': 'flex',
                    'justify-content': 'center',
                    'align-items': 'flex-start',
                    'marginTop': '10px'
                },
                children=[
                    dcc.Input(
                        id={'type':'movie-input', 'index': i},
                        placeholder=f'Sök film #{i+1}',
                        style={
                            'width': '300px',
                            'backgroundColor': '#ffffff',
                            'color': '#000000',
                            'borderRadius': '4px',
                            'border': '1px solid #ccc',
                            'padding': '5px',
                            'textAlign': 'center'
                        }
                    ),
                    dcc.Dropdown(
                        id={'type':'movie-dropdown', 'index': i},
                        style={
                            'width': '340px',
                            'backgroundColor': '#ffffff',
                            'color': '#000000',
                            'borderRadius': '4px',
                            'border': '1px solid #ccc',
                            'marginLeft': '10px'
                        }
                    )
                ]
            )
        )
    return children

@app.callback(
    Output({'type':'movie-dropdown', 'index': ALL}, 'options'),
    Input({'type':'movie-input', 'index': ALL}, 'value')
)
def update_dropdowns(inputs):
    options_list = []
    for val in inputs:
        if not val:
            options_list.append([])
            continue
        matches = search_movies(val)
        if len(matches) > 100:
            options_list.append([{'label': 'Sökningen är för bred, var mer specifik', 'value': None}])
        else:
            options = [{'label': row['title'], 'value': row['index']} for _, row in matches.iterrows()]
            options_list.append(options)
    return options_list

@app.callback(
    Output('recommendations', 'children'),
    Input('rec-btn', 'n_clicks'),
    State({'type':'movie-dropdown', 'index': ALL}, 'value'),
    State('rating-choice', 'value')
)
def recommend(n_clicks, selected_indices, rating_choice):
    selected_indices = [i for i in selected_indices if i is not None]
    if not selected_indices:
        return 'Du måste välja minst en film.'

    rankings = []
    years = []
    ratings_list = []

    for idx in selected_indices:
        rankings.append(get_rankings(idx))
        years.append(movies.iloc[idx]['year'])
        ratings_list.append(movies.iloc[idx]['rating'])
    
    rec_indices = get_recommendations(selected_indices, rankings, years)
    if not rec_indices.any():
        return 'Inga rekommendationer kunde hittas.'

    rec_df = movies.loc[rec_indices, ['title', 'rating', 'imdbId']].copy()

    if rating_choice == 'high':
        rec_df = rec_df.sort_values(by='rating', ascending=False).head(5)
    elif rating_choice == 'low':
        rec_df = rec_df.sort_values(by='rating', ascending=True).head(5)
    elif rating_choice == 'closest':
        mean_rating = sum(ratings_list)/len(ratings_list)
        rec_df['diff'] = abs(rec_df['rating'] - mean_rating)
        rec_df = rec_df.sort_values(by='diff', ascending=True).head(5)

    return [
        html.Div([
        html.A(
            f"{row['title']} — rating: {row['rating']:.1f}",
            href=f"https://www.imdb.com/title/tt{int(row['imdbId']):07d}/",
            target="_blank",
            style={'color': '#00ffff', 'textDecoration': 'none'}
        )
    ]) for _, row in rec_df.iterrows()
]

if __name__ == '__main__':
    app.run(debug=True)