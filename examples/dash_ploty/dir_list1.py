import urllib

from dash import Dash, html, dcc, Input, Output, callback, State
from dash.dash_table import DataTable
import os
from datetime import datetime

app = Dash(__name__)

root_directory = 'inputs/d78c7302-ddf6-443d-b3e0-a619023596c1/b8c6b0c5-5ff3-45e5-99d0-fb2921297cbb'  # Change to your directory path
def get_directories(path):
    """ Returns a list of directories with additional info in a given path """
    directories = []
    try:
        for d in os.listdir(path):
            full_path = os.path.join(path, d)
            if os.path.isdir(full_path):
                file_count = len([f for f in os.listdir(full_path) if os.path.isfile(os.path.join(full_path, f))])
                last_modified = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime('%Y-%m-%d %H:%M:%S')
                url_safe_directory_name = urllib.parse.quote(d)  # URL-encode the directory name
                link = f"[{d}](/directory/{url_safe_directory_name})"
                directories.append({"name": link, "file_count": file_count, "last_modified": last_modified})
    except Exception as e:
        directories = [{"name": f"Error: {str(e)}", "file_count": "N/A", "last_modified": "N/A"}]
    return directories

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.H1("Experiment"),
    DataTable(
        id='directory-table',
        columns=[
            {"name": "Simulation", "id": "simulation_id", "presentation": "markdown"},  # Enable Markdown
            {"name": "Simulation count", "id": "file_count"},
            {"name": "Last Modified", "id": "last_modified"}
        ],
        data=[],
        style_cell={'textAlign': 'left'},
        style_header={
            'backgroundColor': 'white',
            'fontWeight': 'bold'
        },
        style_table={'height': '300px', 'overflowY': 'auto'},
        markdown_options={"html": True}  # Allow HTML content within markdown cells
    ),
    html.Div(id='page-content')
])

@app.callback(
    Output('directory-table', 'data')
    Input('url', 'pathname')
)
def update_table(pathname):
    if pathname == "/" or pathname == "":
        #files = os.listdir(root_directory)
        #[x[0] for x in os.walk(root_directory)]
        return get_directories(root_directory)
    return []

@app.callback(
    Output('page-content', 'children'),
    Input('simulation_id', 'value')
)
def update_output(value):
    if pathname and pathname != "/":
        # List files in the selected directory
        files = os.listdir(pathname)
        return html.Ul([html.Li(file) for file in files])
    return "No directory selected"

if __name__ == '__main__':
    app.run_server(debug=True, port="8052")