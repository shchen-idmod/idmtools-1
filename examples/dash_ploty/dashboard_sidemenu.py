import json
import os
from pathlib import Path
import dash
from dash import Dash, html, dcc, Input, Output, callback, State, callback_context
from dash.dash_table import DataTable
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
from idmtools.core import ItemType
from idmtools.core.platform_factory import Platform
from datetime import datetime

#app = Dash(__name__, suppress_callback_exceptions=True)
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

job_directory = r"C:\Users\sharonch\example_emodpy_malaria\microsporidia"
#job_directory = r"C:\Users\sharonch\example_emodpy_malaria\campaign_sweep"
platform = Platform('FILE', job_directory=job_directory)


def update_fields(sim_id, item_path, item_list):
    job_status_path = Path(item_path).joinpath("job_status.txt")
    insetchart_exists = False
    if not job_status_path.exists():
        status_string = "pending"
    else:
        status = open(job_status_path).read().strip()
        if status == '0':
            status_string = "succeeded"
            insetchart_path = Path(item_path).joinpath("output/InsetChart.json")
            if not insetchart_path.exists():
                insetchart_exists = False
            else:
                insetchart_exists = True
        elif status == '100':
            status_string = "running"
        elif status == '-1':
            status_string = "failed"
        else:
            status_string = "running"
    item_list[2] = status_string
    item_list[4] = insetchart_exists
    return item_list


def build_data(suite_id: None, exp_id: None, sim_id: None):
    data_df = pd.DataFrame(columns=['id', 'tags', 'status', 'last_modified', 'insetchart_exists'])
    data_df.set_index('id', inplace=True)
    # Walk through the directory
    if suite_id is None and exp_id is None and sim_id is None:
        base_dir = job_directory
        data_df.index.name = 'suite_id'
    elif suite_id is not None:
        base_dir = platform.get_directory_by_id(suite_id, ItemType.SUITE)
        data_df.index.name = 'experiment_id'
    elif exp_id is not None:
        base_dir = platform.get_directory_by_id(exp_id, ItemType.EXPERIMENT)
        data_df.index.name = 'simulation_id'
    elif sim_id is not None:
        sim = platform.get_item(sim_id, ItemType.SIMULATION)
        sim_dir = platform.get_directory(sim)
        last_modified = datetime.fromtimestamp(os.path.getmtime(sim_dir)).strftime('%Y-%m-%d %H:%M:%S')
        item_list = [sim_id, str(sim.tags), None, last_modified, False]
        item_list = update_fields(sim_id, sim_dir, item_list)
        ser = pd.Series(item_list, index=['simulation_id', 'tags', 'status', 'last_modified', 'insetchart_exists'])
        sim_df = pd.concat([data_df, pd.DataFrame([ser])], ignore_index=True)
        return sim_df
    for item in os.listdir(base_dir):
        # Construct the full path of the item
        item_path = os.path.join(base_dir, item)
        # Check if this item is a directory
        if os.path.isdir(item_path):
            # if metadata.json exists, read the metadata
            if 'metadata.json' in os.listdir(item_path):
                with open(os.path.join(item_path, 'metadata.json'), 'r') as file:
                    metadata = json.load(file)
                last_modified = datetime.fromtimestamp(os.path.getmtime(item_path)).strftime('%Y-%m-%d %H:%M:%S')
                item_list = [metadata['id'], str(metadata['tags']), metadata['status'], last_modified, False]
                if exp_id is not None:
                    item_list = update_fields(metadata['id'], item_path, item_list)
                ser = pd.Series(item_list, index=['id', 'tags', 'status', 'last_modified', 'insetchart_exists'])
                data_df = pd.concat([data_df, pd.DataFrame([ser])], ignore_index=True)

    data_df.set_index('id', inplace=True)
    if suite_id is None and exp_id is None:
        data_df.index.name = 'suite_id'
    elif suite_id is not None:
        data_df.index.name = 'experiment_id'
    elif exp_id is not None:
        data_df.index.name = 'simulation_id'
    return data_df


df = build_data(suite_id=None, exp_id=None, sim_id=None)


def build_all_experiments(exp_id=None):
    if exp_id is not None:
        exp_df = build_data(suite_id=None, exp_id=exp_id, sim_id=None)
        return exp_df
    else:
        df_copy = df.copy()
        df_copy = df_copy.reset_index()
        data_df = pd.DataFrame(columns=['tags', 'status', 'last_modified', 'insetchart_exists'])
        for suite_id in df_copy['suite_id']:
            exp_df = build_data(suite_id=suite_id, exp_id=None, sim_id=None)
            data_df = pd.concat([data_df, exp_df])
        data_df.index.name = 'experiment_id'
        return data_df


def generate_table_data(dataframe):
    df_copy = dataframe.copy()
    df_copy = df_copy.reset_index()
    if 'suite_id' in df_copy.columns:
        df_copy['details_link'] = df_copy['suite_id'].apply(lambda x: f'[{x}](/suites/{x})')
        df_copy['plot_link'] = df_copy.apply( lambda row: '', axis=1)
    elif 'experiment_id' in df_copy.columns:
        df_copy['details_link'] = df_copy['experiment_id'].apply(lambda x: f'[{x}](/experiments/{x})')
        df_copy['plot_link'] = df_copy.apply( lambda row: '', axis=1)
    elif 'simulation_id' in df_copy.columns:
        df_copy['details_link'] = df_copy['simulation_id'].apply(lambda x: f'[{x}](/simulations/{x})')
        # Create plot chart link if inset chart exists
        df_copy['plot_link'] = df_copy.apply(
            lambda row: f'[Plot Chart](/plot/{row["simulation_id"]})' if row['insetchart_exists'] else '', axis=1
        )
    return df_copy[['details_link', 'tags', 'status', 'last_modified', 'plot_link']].to_dict('records')


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),  # Tracks URL location
    dbc.Row([
        dbc.Col(html.Div([
            html.H2("Idmtools local UI", style={'text-align': 'center'}),
            dbc.Nav([
                dbc.NavLink("Dashboard", href="/", active="exact"),
                dbc.NavLink("Suite", href="/suites", active="exact"),
                dbc.NavLink("Experiment", href="/experiments", active="exact")
            ], vertical=True, pills=True)
        ], style={'background-color': '#f8f9fa', 'height': '100vh', 'padding': '20px'}), width=2),
        dbc.Col(
            html.Div([
            DataTable(
                id='table',
                columns=[
                    {"name": "ID", "id": "details_link", "presentation": "markdown"},
                    {"name": "Tags", "id": "tags"},
                    {"name": "Status", "id": "status"},
                    {"name": "Last Modified", "id": "last_modified"},
                    {"name": "Inset Chart", "id": "plot_link", "presentation": "markdown"},
                ],
                data=generate_table_data(df),
                markdown_options={"html": True},
                style_cell={'textAlign': 'left', 'padding': '5px'},
                style_table={'height': '500px', 'overflowY': 'auto'},
                style_data_conditional=[
                    {'if': {'column_id': 'sim_id_link'}, 'cursor': 'pointer'},
                    {'if': {'column_id': 'plot_link', 'filter_query': '{plot_link} ne ""'}, 'cursor': 'pointer'}
                ]
            ),
            html.Div(id='page-content')], style={'padding': '20px'}), width=10)
    ])
])


@app.callback(
    Output('url', 'pathname'),
    Input('page-dropdown', 'value')
)
def update_url(value):
    if not callback_context.triggered:
        return dash.no_update  # No input has triggered the callback
    triggered_id, triggered_prop = callback_context.triggered[0]['prop_id'].split('.')
    if triggered_id == 'page-dropdown' and triggered_prop == 'value':
        return f'/{value}' if value else '/'
    return dash.no_update

@app.callback(
    [Output('page-content', 'children'),
     Output('table', 'data'),
     Output('table', 'style_table')],
    Input('url', 'pathname')
)
def display_page(pathname):
    # get data again for refresh
    item_id = pathname.split('/')[-1]
    if pathname == '/' or pathname == '/suites':
        suite_df = build_data(suite_id=None, exp_id=None, sim_id=None)
        return html.Div(html.H1('Welcome Home!')), generate_table_data(suite_df), {'height': '500px', 'overflowY': 'auto'}
    elif pathname.startswith('/suites/'):
        suite_id = item_id
        exp_df = build_data(suite_id=suite_id, exp_id=None, sim_id=None)
        return html.Div(html.H1('Welcome exp!')), generate_table_data(exp_df), {'height': '500px', 'overflowY': 'auto'}
    elif pathname == '/experiments':
        exp_df = build_all_experiments(exp_id=None)
        return html.Div(html.H1('Welcome experiments!')), generate_table_data(exp_df), {'height': '500px', 'overflowY': 'auto'}
    elif pathname.startswith('/experiments/'):
        exp_id = item_id
        sim_df = build_data(suite_id=None, exp_id=exp_id, sim_id=None)
        return "", generate_table_data(sim_df), {'height': '500px', 'overflowY': 'auto'}
    elif pathname.startswith('/simulations/'):
        sim_id = item_id
        row = build_data(suite_id=None, exp_id=None, sim_id=sim_id)
        if not row.empty:
            return html.Div([
                html.H3(f"Details for Simulation ID: {sim_id}"),
                html.P(f"Status: {row.iloc[0]['status']}"),
                html.P(f"Last Modified: {row.iloc[0]['last_modified']}"),
                html.P(f"Inset Chart Exists: {'Yes' if row.iloc[0]['insetchart_exists'] else 'No'}")
            ]), generate_table_data(row), {'height': '100px', 'overflowY': 'auto'}
        return html.Div("No data available for this Simulation ID."), [], {'height': '100px', 'overflowY': 'auto'}
    elif pathname.startswith('/plot/'):
        sim_id = item_id
        sim = platform.get_item(sim_id, ItemType.SIMULATION)
        sim_dir = platform.get_directory(sim)
        row = build_data(suite_id=None, exp_id=None, sim_id=sim_id)
        chart_path = os.path.join(sim_dir, "output", "InsetChart.json")
        if os.path.exists(chart_path):
            with open(chart_path, 'r') as file:
                data = json.load(file)
            channel_data = {}
            channel_names = []

            # Extract data for each channel
            for channel, details in data['Channels'].items():
                channel_data[channel] = details['Data']
                channel_names.append(channel)

            return html.Div([
                html.H4('Inset Chart for Simulation: {}'.format(sim_id)),
                dcc.Dropdown(
                    id='channel-selector',
                    options=[{'label': name, 'value': name} for name in channel_names],
                    value=channel_names[0] if channel_names else None,  # Default to first channel
                    clearable=False,
                    style={'width': '300px'}
                ),
                dcc.Graph(id='chart')]), generate_table_data(row), {'height': '100px', 'overflowY': 'auto'}
    return "", generate_table_data(df), {'height': '500px', 'overflowY': 'auto'}


@app.callback(
    Output('chart', 'figure'),
    [Input('channel-selector', 'value'),
     Input('url', 'pathname')]
)
def update_graph(selected_channel, pathname):
    if pathname.startswith('/plot/'):
        sim_id = pathname.split('/')[-1]
        sim = platform.get_item(sim_id, ItemType.SIMULATION)
        sim_dir = platform.get_directory(sim)
        chart_path = os.path.join(sim_dir, "output", "InsetChart.json")
        if os.path.exists(chart_path):
            with open(chart_path, 'r') as file:
                data = json.load(file)
            channel_data = {}
            channel_names = []

            # Extract data for each channel
            for channel, details in data['Channels'].items():
                channel_data[channel] = details['Data']
                channel_names.append(channel)
            ic_df = pd.DataFrame(channel_data)
            ic_df.reset_index(inplace=True)
            ic_df.rename(columns={'index': 'Time Step'}, inplace=True)
            fig = px.line(ic_df, x='Time Step', y=selected_channel)
            fig.update_xaxes(minor=dict(ticks="inside", showgrid=True))
            fig.update_xaxes(rangeslider_visible=True)
            fig.update_layout(plot_bgcolor='black', paper_bgcolor='lightblue', font_color='white')
            return fig

    return px.line()  # Return an empty plot if no data is available

if __name__ == '__main__':
    app.run_server(debug=True, port="8054")
