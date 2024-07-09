import urllib

from dash import Dash, html, dcc, Input, Output, callback, State
from dash.dash_table import DataTable
import os
from datetime import datetime

app = Dash(__name__)

root_directory = 'inputs/d78c7302-ddf6-443d-b3e0-a619023596c1/b8c6b0c5-5ff3-45e5-99d0-fb2921297cbb'  # Change to your directory path
def find_file(path, file_name):
    for root, dirs, files in os.walk(path):
        if file_name in files:
            return os.path.join(root, file_name)
    return None

def get_job_status(job_status_path):
    if job_status_path:
        with open(job_status_path) as f:
            return f.read()
    return "N/A"
def get_directories(path):
    """ Returns a list of directories with additional info in a given path """
    directories = []
    try:
        for d in os.listdir(path):
            full_path = os.path.join(path, d)
            if os.path.isdir(full_path):
                job_status_path = find_file(full_path, "job_status.txt")
                last_modified = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime('%Y-%m-%d %H:%M:%S')
                url_safe_directory_name = urllib.parse.quote(d)  # URL-encode the directory name
                link = f"[{d}](/simulation/{url_safe_directory_name})"
                directories.append({"name": link, "status": get_job_status(job_status_path), "last_modified": last_modified})
    except Exception as e:
        directories = [{"name": f"Error: {str(e)}", "file_count": "N/A", "last_modified": "N/A"}]
    return directories

app.layout = html.Div([
    dcc.Location(id='url', refresh=True),
    html.H1("Experiment"),
    DataTable(
        id='directory-table',
        columns=[
            {"name": "Simulation", "id": "name", "presentation": "markdown"},  # Enable Markdown
            {"name": "Status", "id": "status"},
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
    [Output('directory-table', 'data'),
     Output('directory-table', 'style_table')],
    Input('url', 'pathname')
)
def update_table(pathname):
    if pathname == "/" or pathname == "":
        return get_directories(root_directory), {'height': '300px', 'overflowY': 'auto'}
    elif pathname.startswith("/simulation/"):
        full_path = os.path.join(root_directory, os.path.basename(pathname))
        job_status_path = find_file(full_path, "job_status.txt")
        last_modified = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime('%Y-%m-%d %H:%M:%S')
        return [{"name": os.path.basename(pathname), "status": get_job_status(job_status_path), "last_modified": last_modified}], {'height': '100px', 'overflowY': 'auto'}
    return []


@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname.startswith("/simulation/"):
        files = os.listdir(os.path.join(root_directory, os.path.basename(pathname)))
        return html.Div([html.Ul([html.Li(file) for file in files])])
    return "Click on a simulation for more details."

if __name__ == '__main__':
    app.run_server(debug=True, port="8051")