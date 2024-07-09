import os

import dash
from dash import html, dcc
from dash.dependencies import Input, Output

app = dash.Dash(__name__)

base_path = 'inputs'
directory_list = [os.path.join(base_path, d) for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
# Dropdown to select a directory
app.layout = html.Div([
    dcc.Dropdown(
        id='directory-dropdown',
        options=[{'label': os.path.basename(d), 'value': d} for d in directory_list],
        value=directory_list[0] if directory_list else None
    ),
    html.Div(id='directory-output')
])

@app.callback(
    Output('directory-output', 'children'),
    Input('directory-dropdown', 'value')
)
def update_output(selected_directory):
    if selected_directory:
        # List files in the selected directory
        files = os.listdir(selected_directory)
        return html.Ul([html.Li(file) for file in files])
    return "No directory selected"

if __name__ == '__main__':
    app.run_server(debug=True)
