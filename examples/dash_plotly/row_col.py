import dash
from dash import Dash, html, dcc
from dash import dash_table
import dash_bootstrap_components as dbc
from dash.dash_table import DataTable

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.Div([
            html.Div(id='page-right', style={'padding': '20px'}),
            DataTable(
                id='table',
                columns=[{"name": i, "id": i} for i in ['Column 1', 'Column 2', 'Column 3']],
                data=[
                    {"Column 1": "Row 1", "Column 2": "Data 1", "Column 3": "Something"},
                    {"Column 1": "Row 2", "Column 2": "Data 2", "Column 3": "Something else"}
                ]
            )
        ]), width=10)
    ])
])
if __name__ == '__main__':
    app.run_server(debug=True)
