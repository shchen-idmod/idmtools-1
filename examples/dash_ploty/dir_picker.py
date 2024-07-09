from dash import Dash, html, dcc, Input, Output, State, callback
import os

app = Dash(__name__)

# Starting directory
initial_path = os.getcwd()

app.layout = html.Div([
    dcc.Input(id='path-input', type='text', value=initial_path, style={'width': '80%'}),
    html.Button('Go', id='go-button', n_clicks=0),
    dcc.Dropdown(id='directory-selector', options=[], style={'width': '80%'}),  # Dropdown for directory selection
    html.Div(id='selected-directory')  # Placeholder to display the selected directory or navigate further
])

@app.callback(
    Output('directory-selector', 'options'),
    Input('go-button', 'n_clicks'),
    State('path-input', 'value'),
)
def update_directory_list(n_clicks, path):
    if n_clicks == 0:
        return []
    if not os.path.exists(path):
        return [{'label': 'Path does not exist.', 'value': ''}]
    # List directories only
    directories = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    return [{'label': d, 'value': os.path.join(path, d)} for d in directories]

@app.callback(
    Output('selected-directory', 'children'),
    Input('directory-selector', 'value'),
)
def display_directory_content(dir_path):
    if not dir_path or not os.path.isdir(dir_path):
        return "No directory selected or it does not exist."
    return html.Div(f"Selected Directory: {dir_path}")

if __name__ == '__main__':
    app.run_server(debug=True, port="8053")
