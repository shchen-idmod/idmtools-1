from dash import Dash, html, dcc, Input, Output
import urllib

app = Dash(__name__)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.H1("URL Information"),
    html.Div(id='url-content'),
    html.Div(id='search-content')
])
from urllib.parse import parse_qs, urlparse


@app.callback(
    [Output('url-content', 'children'),
     Output('search-content', 'children')],
    [Input('url', 'pathname'),
     Input('url', 'search')]
)
def display_url_and_search(pathname, search):
    # Display the pathname directly
    url_info = f"Current Pathname: {pathname}"

    # Parse the query string
    query_params = parse_qs(urlparse(search).query)
    search_info = "Search Params: "
    # Iterate through the query parameters to format them nicely
    for param, values in query_params.items():
        search_info += f"{param} = {values[0]}, "

    # Strip the extra comma and space at the end if present
    search_info = search_info.strip(", ")

    return url_info, search_info
if __name__ == '__main__':
    app.run_server(debug=True)
