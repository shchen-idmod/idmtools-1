from dash import Dash, html, dcc
from dash.dependencies import Input, Output, State

app = Dash(__name__)

app.layout = html.Div([
    dcc.Input(id='path-input', type='text', style={'width': '80%'}),
    html.Button('Browse', id='browse-button', n_clicks=0),
    html.Input(id='file-input', type='file', style={'display': 'none'}),  # Correct usage of html.Input for file type
    html.Div(id='file-path-display')
])

@app.callback(
    Output('file-input', 'style'),
    Input('browse-button', 'n_clicks'),
    prevent_initial_call=True
)
def trigger_file_dialog(n_clicks):
    if n_clicks > 0:
        return {}  # Show the file input dialog
    return {'display': 'none'}  # Keep hidden otherwise

@app.callback(
    Output('file-path-display', 'children'),
    Input('file-input', 'files'),
    prevent_initial_call=True
)
def display_selected_file(files):
    if files:
        return f"Selected File: {files[0]['name']}"  # Access file name from files dictionary
    return "No file selected"

if __name__ == '__main__':
    app.run_server(debug=True, port='8053')
