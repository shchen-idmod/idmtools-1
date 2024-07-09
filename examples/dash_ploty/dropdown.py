import dash
import pandas as pd
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc


import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

# Placeholder DataFrames
df_suites = pd.DataFrame({
    "Suite ID": ["001", "002"],
    "Name": ["Login Test", "Load Test"],
    "Description": ["Tests login functionality", "Tests system under heavy load"]
})

df_experiments = pd.DataFrame({
    "Experiment ID": ["E001", "E002"],
    "Name": ["Chemical Resistance", "Heat Exposure"],
    "Description": ["Tests resistance to chemicals", "Tests tolerance to high temperatures"]
})

df_simulations = pd.DataFrame({
    "Simulation ID": ["S001", "S002"],
    "Name": ["Traffic Patterns", "Economic Forecast"],
    "Description": ["Simulates vehicle traffic patterns", "Forecasts economic conditions"]
})


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Dropdown(
        id='page-dropdown',
        options=[
            {'label': 'Suites', 'value': 'suites'},
            {'label': 'Experiments', 'value': 'experiments'},
            {'label': 'Simulations', 'value': 'simulations'}
        ],
        value='suites',  # Default value
        style={'width': '50%'}
    ),
    html.Div(id='page-content')
])

@app.callback(
    Output('url', 'pathname'),
    Input('page-dropdown', 'value')
)
def update_url(value):
    if value:
        return f'/{value}'
    return '/'

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname:
        page_type = pathname.strip('/')
        if page_type in ['suites', 'experiments', 'simulations']:
            return html.Div([
                html.H1(f'{page_type.capitalize()} Page'),
                dbc.Table.from_dataframe(generate_df(page_type), striped=True, bordered=True, hover=True)
            ])
        elif pathname == '/':
            return html.Div([
                html.H1('Welcome to the Dynamic Pages Dashboard'),
                html.P("Select a page type from the dropdown to view details.")
            ])
    return html.Div("No page selected")

def generate_df(page_type):
    data = {
        'suites': pd.DataFrame({
            "Suite ID": ["001", "002"],
            "Name": ["Login Test", "Load Test"],
            "Description": ["Tests login functionality", "Tests system under heavy load"]
        }),
        'experiments': pd.DataFrame({
            "Experiment ID": ["E001", "E002"],
            "Name": ["Chemical Resistance", "Heat Exposure"],
            "Description": ["Tests resistance to chemicals", "Tests tolerance to high temperatures"]
        }),
        'simulations': pd.DataFrame({
            "Simulation ID": ["S001", "S002"],
            "Name": ["Traffic Patterns", "Economic Forecast"],
            "Description": ["Simulates vehicle traffic patterns", "Forecasts economic conditions"]
        })
    }
    return data.get(page_type, pd.DataFrame())

if __name__ == '__main__':
    app.run_server(debug=True, port="8050")