import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the app layout
# app.layout = html.Div([
#     dbc.Row([
#         dbc.Col(html.Div("Side Menu", style={'background-color': '#f8f9fa', 'height': '100vh', 'padding': '20px'}), width=2),
#         dbc.Col(html.Div("Main Content Area", style={'padding': '20px'}), width=10)
#     ])
# ])
import dash
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the layout of the app
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),  # Tracks URL location
    dbc.Row([
        dbc.Col(html.Div([
            html.H2("Menu", style={'text-align': 'center'}),
            dbc.Nav([
                dbc.NavLink("Home", href="/", active="exact"),
                dbc.NavLink("Page 1", href="/page-1", active="exact"),
                dbc.NavLink("Page 2", href="/page-2", active="exact")
            ], vertical=True, pills=True)
        ], style={'background-color': '#f8f9fa', 'height': '100vh', 'padding': '20px'}), width=2),
        dbc.Col(html.Div(id='page-content', style={'padding': '20px'}), width=10)
    ])
])

# Callback to update page content based on URL
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/page-1':
        return html.Div([
            html.H1('Page 1'),
            html.P('Welcome to Page 1!')
        ])
    elif pathname == '/page-2':
        return html.Div([
            html.H1('Page 2'),
            html.P('Welcome to Page 2!')
        ])
    else:
        return html.Div([
            html.H1('Home'),
            html.P('Welcome to the Home Page!')
        ])


if __name__ == '__main__':
    app.run_server(debug=True)
