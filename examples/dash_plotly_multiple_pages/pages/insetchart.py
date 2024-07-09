# Only need to "pip install dash plotly"
import json

# from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import dash
from dash import html, dcc, callback, Input, Output

#app = Dash(__name__)

dash.register_page(__name__)
# Load JSON data
with open('inputs/1/InsetChart.json', 'r') as file:
    data = json.load(file)

channel_data = {}
channel_names = []

# Extract data for each channel
for channel, details in data['Channels'].items():
    channel_data[channel] = details['Data']
    channel_names.append(channel)

# Convert the dictionary into a DataFrame
df = pd.DataFrame(channel_data)

# Reset index to get the timestep as a column
df.reset_index(inplace=True)
df.rename(columns={'index': 'Time Step'}, inplace=True)

layout = html.Div([
    html.H4('Inset Chart'),
    html.P("Select Channel:"),
    dcc.Dropdown(
        id="time-series-x-ticker",
        options=channel_names,
        value="Infectious Vectors",  # default to this channel
        clearable=False,
    ),
    dcc.Graph(id="time-series-x-time-series-chart")

])


@callback(
    Output("time-series-x-time-series-chart", "figure"),
    Input("time-series-x-ticker", "value"))
def display_time_series(ticker):
    fig = px.line(df, x='Time Step', y=ticker)
    fig.update_xaxes(minor=dict(ticks="inside", showgrid=True))
    fig.update_xaxes(rangeslider_visible=True)
    return fig



