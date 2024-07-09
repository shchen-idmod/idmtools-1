import os

import dash
from dash import html, dcc
from dash.dependencies import Input, Output

app = dash.Dash(__name__)

# Assuming a fixed list of directories for the dropdown
directory_list = ['inputs/d78c7302-ddf6-443d-b3e0-a619023596c1/b8c6b0c5-5ff3-45e5-99d0-fb2921297cbb/0696e162-353c-4d57-b5d0-d6224a2c51a5']
def list_directory_contents(directory):
    files = []
    subdirs = []
    for entry in os.listdir(directory):
        full_path = os.path.join(directory, entry)
        if os.path.isdir(full_path):
            subdirs.append(entry)  # Add subdir name, not path
        elif os.path.isfile(full_path):
            files.append(entry)  # Add filename, not path
    return files, subdirs

app.layout = html.Div([
    dcc.Dropdown(
        id='directory-dropdown',
        options=[{'label': os.path.basename(d), 'value': d} for d in directory_list],
        value=None
    ),
    html.H3('Directories:'),
    html.Ul(id='directory-list'),
    html.H3('Files:'),
    html.Ul(id='file-list')
])

@app.callback(
    [Output('file-list', 'children'),
     Output('directory-list', 'children')],
    [Input('directory-dropdown', 'value')]
)
def update_output(selected_directory):
    if selected_directory:
        files, subdirs = list_directory_contents(selected_directory)
        files_html = [html.Li(file) for file in files]
        subdirs_html = [html.Li(subdir) for subdir in subdirs]
        return files_html, subdirs_html
    return [], []

if __name__ == '__main__':
    app.run_server(debug=True)
