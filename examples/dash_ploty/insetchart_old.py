# pip install dash and plotly
import json

from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
app = Dash(__name__)

# ic_df = pd.read_json('inputs/InsetChart.json')
# df = ic_df[ic_df['Channels'].notna()]
# new_df =pd.DataFrame(df['Channels'].tolist(), index=df['Channels'])
# df1=df['Channels'].apply(lambda x: list(x.values())[1])
# expanded_df = pd.DataFrame(df1.values.tolist(), index=df1.index)
# expanded_df.reset_index(inplace=True)
# expanded_df.rename(columns={'index': 'Channels'}, inplace=True)
# expanded_df.set_index('Channels', inplace=True)
# melted_df = expanded_df.reset_index().melt(id_vars=['Channels'])
# pivoted_df = melted_df.pivot(index='variable', columns='Channels', values='value').reset_index().rename(columns={'variable': 'Time'})
# Load JSON data
with open('inputs/InsetChart.json', 'r') as file:
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

app.layout = html.Div([
    html.H4('Inset chart example'),
    dcc.Graph(id="time-series-x-time-series-chart"),
    html.P("Select channel:"),
    dcc.Dropdown(
        id="time-series-x-ticker",
        options=channel_names,
        value="Infectious Vectors",  # default to this channel
        clearable=False,
    ),
])


@app.callback(
    Output("time-series-x-time-series-chart", "figure"),
    Input("time-series-x-ticker", "value"))
def display_time_series(ticker):
    fig = px.line(df, x='Time Step', y=ticker)
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
