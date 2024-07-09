import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

# Create a Dash application
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([
    dbc.Button(
        "Open Folder",
        id='open-folder-btn',
        className="mb-3",
        color="primary",
        n_clicks=0
    ),
    html.Div(id='output-container')
])

# Add callback to handle button click
@app.callback(
    dash.dependencies.Output('output-container', 'children'),
    [dash.dependencies.Input('open-folder-btn', 'n_clicks')]
)
def on_button_click(n):
    if n > 0:
        # Normally here you would handle file operations or similar,
        # but for web applications, consider opening a new tab with predefined content.
        return html.A("Go to Files", href="http://example.com/files", target="_blank")
    return "Click the button to go to the files page."
if __name__ == '__main__':
    app.run_server(debug=True)
