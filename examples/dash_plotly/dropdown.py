import dash
from dash import Dash, dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout includes a Location component for capturing URL changes
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dbc.Row([
        dbc.Col(html.Div([
            html.H2("Menu"),
            dcc.Link('Home', href='/', style={'display': 'block'}),
            dcc.Link('Suites', href='/suites', style={'display': 'block'})
        ]), width=2),
        dbc.Col(html.Div(id='page-content'), width=10)
    ])
])
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/':
        return html.H1('Welcome Home!')
    elif pathname == '/suites':
        # Example content: List of suites with links
        suites_list = [
            {'id': 1, 'name': 'Suite 1'},
            {'id': 2, 'name': 'Suite 2'},
            {'id': 3, 'name': 'Suite 3'}
        ]
        return html.Div([
            html.H1('All Suites'),
            html.Ul([html.Li(dcc.Link(suite['name'], href=f'/suites/{suite["id"]}')) for suite in suites_list])
        ])
    elif pathname.startswith('/suites/'):
        suite_id = pathname.split('/')[-1]
        # Here you would fetch the suite details based on suite_id from your database or data source
        return html.Div([
            html.H1(f'Suite Details for ID: {suite_id}'),
            html.P('More details would go here, potentially fetched from a database.')
        ])
    else:
        return '404'

if __name__ == '__main__':
    app.run_server(debug=True)
