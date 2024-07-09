import json

import dash
from dash import html, dcc, Input, Output, callback, State, ALL
import dash_bootstrap_components as dbc
import os
from dash.exceptions import PreventUpdate

# Optional for more advanced functionalities
import pandas as pd
def list_directory(path):
    """List files and directories in a given path, returning safe paths for JSON."""
    files = []
    directories = []
    for item in os.listdir(path):
        full_path = os.path.join(path, item)
        if os.path.isfile(full_path):
            files.append(full_path)
        else:
            directories.append(full_path)

    safe_directories = [d for d in directories]
    safe_files = [f for f in files]
    return safe_directories, safe_files

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("File Explorer"),
            dcc.Dropdown(id='drive-dropdown', options=[
                {'label': 'C:/', 'value': 'C:/'},
                # Add other drives or paths as needed
            ], value='C:/'),
            dcc.Store(id='current-path', data={'path': 'C:/'}),  # Store current path
            html.Div(id='file-list')
        ], width=12)
    ])
])

@callback(
    Output('file-list', 'children'),
    Input('drive-dropdown', 'value'),
    Input('current-path', 'data')
)
def update_file_list(selected_drive, current_data):
    ctx = dash.callback_context

    # If triggered by drive dropdown, reset to base path of the drive
    if not ctx.triggered or ctx.triggered[0]['prop_id'] == 'drive-dropdown.value':
        path = selected_drive
    else:
        if not current_data or 'path' not in current_data:
            raise PreventUpdate
        path = current_data['path']

    directories, files = list_directory(path)
    return html.Ul([
        html.Li(html.A(d, href='#', id={'type': 'dir-link', 'index': os.path.join(path, d)}))
        for d in directories
    ] + [html.Li(f) for f in files])

@callback(
    Output('current-path', 'data'),
    Input({'type': 'dir-link', 'index': ALL}, 'n_clicks'),
    State('current-path', 'data'),
    prevent_initial_call=True
)
def update_current_path(clicks, current_data):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    # Get the clicked directory from the component id
    if not any(clicks):
        clicked_dir = ctx.triggered[0]['prop_id'].split('.')[0] + '"}'
    else:
        clicked_dir = ctx.triggered[0]['prop_id'].split('.')[0]

    # Safely parse the JSON string
    try:
        clicked_dir_dict = json.loads(clicked_dir)
        new_path = clicked_dir_dict['index']
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        raise PreventUpdate  # Prevent the callback from updating if there's an error

    return {'path': new_path}

if __name__ == '__main__':
    app.run_server(debug=True)
