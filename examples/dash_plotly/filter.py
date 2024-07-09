from dash import Dash, dcc, html
import pandas as pd
from urllib.parse import parse_qs, urlparse
from dash.dependencies import Input, Output
app = Dash(__name__)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='content')
])


@app.callback(
    Output('content', 'children'),
    Input('url', 'search'),
    allow_duplicate=True
)
def display_page(search):
    query_params = parse_qs(urlparse(search).query)
    filter_id = query_params.get('filters', [''])[0]  # Default to empty string if not found
    if filter_id:
        # Assuming the format 'Id=value', you might need to further parse if necessary
        filter_key, filter_value = filter_id.split('=') if '=' in filter_id else (None, None)
        if filter_key == 'Id':
            # Fetch data or filter your DataFrame based on this ID
            # Here, we just display the ID for demonstration
            return f"Displaying data for suite with Id: {filter_value}"
        else:
            return "Id not found in filters"
    return "No filters provided"


# Sample DataFrame
df = pd.DataFrame({
    'Id': ['8a3220af-2624-ef11-aa14-b88303911bc1', 'other-id-1', 'other-id-2'],
    'Name': ['Suite 1', 'Suite 2', 'Suite 3']
})

def get_suite_by_id(suite_id):
    suite = df[df['Id'] == suite_id]
    if not suite.empty:
        return html.Div([
            html.H1(f"Suite Name: {suite.iloc[0]['Name']}"),
            html.P(f"Suite Id: {suite.iloc[0]['Id']}")
        ])
    else:
        return "No suite matches the provided Id."
# @app.callback(
#     Output('content', 'children'),
#     Input('url', 'search')
# )
# def display_page(search):
#     query_params = parse_qs(urlparse(search).query)
#     filter_id = query_params.get('filters', [''])[0]
#     if filter_id:
#         filter_key, filter_value = filter_id.split('=') if '=' in filter_id else (None, None)
#         if filter_key == 'Id':
#             return get_suite_by_id(filter_value)
#         else:
#             return "Invalid filter key."
#     return "No filters provided"
if __name__ == '__main__':
    app.run_server(debug=True)
