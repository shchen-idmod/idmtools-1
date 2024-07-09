import json
import os

from dash import Dash, html, dcc, Input, Output, callback, State
from dash.dash_table import DataTable
import pandas as pd
import plotly.express as px

from idmtools.core import ItemType
from idmtools.core.platform_factory import Platform
from datetime import datetime

app = Dash(__name__, suppress_callback_exceptions=True)

#job_directory = "C:\github\idmtools\examples\dash_ploty\inputs"
job_directory = r"C:\Users\sharonch\example_emodpy_malaria\campaign_sweep"
platform = Platform('FILE', job_directory=job_directory)
#exp_id = "b8c6b0c5-5ff3-45e5-99d0-fb2921297cbb"
exp_id = "232781a8-bd86-4ada-8b98-33d3b4d08bc5"
exp_dir = platform.get_directory_by_id(exp_id, ItemType.EXPERIMENT)

def get_data(exp_id):
    exp = platform.get_item(exp_id, ItemType.EXPERIMENT)
    status_dict = {}
    df = pd.DataFrame(columns=['sim_id', 'tags', 'status', 'last_modified', 'insetchart_exists'])

    for sim in exp.simulations:
        insetchart_exists = False
        sim_dir = platform.get_directory(sim)
        last_modified = datetime.fromtimestamp(os.path.getmtime(sim_dir)).strftime('%Y-%m-%d %H:%M:%S')
        job_status_path = sim_dir.joinpath("job_status.txt")
        if not job_status_path.exists():
            status_dict[sim.id] = "pending"
        else:
            status = open(job_status_path).read().strip()
            if status == '0':
                status_dict[sim.id] = "succeeded"
                insetchart_path = sim_dir.joinpath("output/InsetChart.json")
                if not insetchart_path.exists():
                    insetchart_exists = False
                else:
                    insetchart_exists = True
            elif status == '100':
                status_dict[sim.id] = "running"
            elif status == '-1':
                status_dict[sim.id] = "failed"
            else:
                status_dict[sim.id] = "running"
        tags = str(sim.tags)
        list = [sim.id, tags, status_dict[sim.id], last_modified, insetchart_exists]
        ser = pd.Series(list, index=['sim_id', 'tags', 'status', 'last_modified', 'insetchart_exists'])
        df = pd.concat([df, pd.DataFrame([ser])], ignore_index=True)
    return df

# Get init data
df = get_data(exp_id)

def generate_table_data(dataframe):
    dataframe = dataframe.copy()
    # Create sim_id details link
    dataframe['details_link'] = dataframe['sim_id'].apply(lambda x: f'[{x}](/simulations/{x})')
    # Create plot chart link if inset chart exists
    dataframe['plot_link'] = dataframe.apply(
        lambda row: f'[Plot Chart](/plot/{row["sim_id"]})' if row['insetchart_exists'] else '', axis=1
    )
    return dataframe[['details_link', 'tags', 'status', 'last_modified', 'plot_link']].to_dict('records')


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.H1('Simulation Dashboard'),
    html.H2('Simulations'),
    DataTable(
        id='table',
        columns=[
            {"name": "Simulation ID", "id": "details_link", "presentation": "markdown"},
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
    html.Div(id='page-content')
])

@app.callback(
    [Output('page-content', 'children'),Output('table', 'data'), Output('table', 'style_table')],
    Input('url', 'pathname')
)
def display_page(pathname):
    # get data again for refresh
    df = get_data(exp_id)
    if pathname.startswith('/simulations/'):
        sim_id = pathname.split('/')[-1]
        row = df[df['sim_id'] == sim_id]
        if not row.empty:
            return html.Div([
                html.H3(f"Details for Simulation ID: {sim_id}"),
                html.P(f"Status: {row.iloc[0]['status']}"),
                html.P(f"Last Modified: {row.iloc[0]['last_modified']}"),
                html.P(f"Inset Chart Exists: {'Yes' if row.iloc[0]['insetchart_exists'] else 'No'}")
            ]), generate_table_data(row), {'height': '100px', 'overflowY': 'auto'}
        return html.Div("No data available for this Simulation ID."), [], {'height': '100px', 'overflowY': 'auto'}
    elif pathname.startswith('/plot/'):
        sim_id = pathname.split('/')[-1]
        row = df[df['sim_id'] == sim_id]
        sim_dir = os.path.join(exp_dir, sim_id)
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
            dff = pd.DataFrame(channel_data)

            dff.reset_index(inplace=True)
            dff.rename(columns={'index': 'Time Step'}, inplace=True)

            return html.Div([
                html.H4('Inset Chart for Simulation: {}'.format(sim_id)),
                dcc.Dropdown(
                    id='channel-selector',
                    options=[{'label': name, 'value': name} for name in channel_names],
                    value=channel_names[0] if channel_names else None,  # Default to first channel
                    clearable=False,
                ),
                dcc.Graph(id='chart')]), generate_table_data(row), {'height': '100px', 'overflowY': 'auto'}
    return "", generate_table_data(df), {'height': '500px', 'overflowY': 'auto'}


@app.callback(
    Output('chart', 'figure'),
    [Input('channel-selector', 'value'), Input('url', 'pathname')]
)
def update_graph(selected_channel, pathname):
    if pathname.startswith('/plot/'):
        sim_id = pathname.split('/')[-1]
        sim_dir = os.path.join(exp_dir, sim_id)
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
            dfx = pd.DataFrame(channel_data)
            dfx.reset_index(inplace=True)
            dfx.rename(columns={'index': 'Time Step'}, inplace=True)
            fig = px.line(dfx, x='Time Step', y=selected_channel)
            fig.update_xaxes(minor=dict(ticks="inside", showgrid=True))
            fig.update_xaxes(rangeslider_visible=True)
            return fig

    return px.line()  # Return an empty plot if no data is available
if __name__ == '__main__':
    app.run_server(debug=True, port="8054")
