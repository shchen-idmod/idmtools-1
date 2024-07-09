from dash import Dash, html, dcc, Input, Output, State, callback
import os

app = Dash(__name__)

# Starting directory
initial_path = os.getcwd()

app.layout = html.Div([
    dcc.Input(id='path-input', type='text', value=initial_path, style={'width': '80%'}),
    html.Button('Go', id='go-button', n_clicks=0),
    dcc.Dropdown(id='file-selector', options=[], style={'width': '80%'}),  # Dropdown for file selection
    html.Div(id='selected-file-content')  # Placeholder to display the content or info of the selected file
])

@app.callback(
    Output('file-selector', 'options'),
    Input('go-button', 'n_clicks'),
    State('path-input', 'value'),
)
def update_file_list(n_clicks, path):
    if n_clicks == 0:
        return []
    if not os.path.exists(path):
        return [{'label': 'Path does not exist.', 'value': ''}]
    files = os.listdir(path)
    return [{'label': f, 'value': os.path.join(path, f)} for f in files]

@app.callback(
    Output('selected-file-content', 'children'),
    Input('file-selector', 'value'),
)
def show_file_content(file_path):
    if not file_path or not os.path.isfile(file_path):
        return "No file selected or file does not exist."
    # Assuming files are readable text for simplicity
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return html.Pre(content)
    except Exception as e:
        return f"Error reading file: {str(e)}"

if __name__ == '__main__':
    app.run_server(debug=True, port="8053")
