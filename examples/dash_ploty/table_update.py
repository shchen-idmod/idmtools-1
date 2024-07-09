from dash import Dash, html, dcc, Input, Output, callback
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
                directories.append((d, file_count, last_modified))
    except Exception as e:
        directories = [(f"Error accessing the directory: {str(e)}", 0, '')]
    return directories

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.H1("Directory Listing"),
    html.Ul(id='directory-list'),
    html.Div(id='page-content')
])

@app.callback(
    Output('directory-list', 'children'),
    Input('url', 'pathname')
)
def list_directories(pathname):
    if pathname == "/" or pathname == "":
        subdirectories = get_directories(root_directory)
        return [html.Li([
            dcc.Link(f"{name} - Files: {count}, Last Modified: {mod_date}", href=f"/{name}")
        ]) for name, count, mod_date in subdirectories]
    return []

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname and pathname != "/":
        # Display details or process something specific for each directory
        return html.Div([
            html.H3(f"Viewing {pathname.strip('/')}")
            # Implement more detailed view or functionalities as required
        ])
    return "Click on a directory name for more details."

if __name__ == '__main__':
    app.run_server(debug=True)
