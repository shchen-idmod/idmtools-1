import pandas as pd
import json
import plotly.express as px

# Load JSON data
with open('inputs/InsetChart.json', 'r') as file:
    data = json.load(file)

# Initialize an empty dictionary to collect the data
channel_data = {}
channel_names = []

# Extract data for each channel
for channel, details in data['Channels'].items():
    channel_data[channel] = details['Data']
    channel_names.append(channel)

# Convert the dictionary into a DataFrame
df = pd.DataFrame(channel_data)

# Optionally, reset index to get the timestep as a column
df.reset_index(inplace=True)
df.rename(columns={'index': 'Time'}, inplace=True)
df.set_index("Time")
df.columns.name = "channel"
df = pd.melt(df, id_vars=['Time'], var_name='channel', value_name='value')
fig = px.area(df, x='Time', y='value', facet_col="channel", facet_col_wrap=5)
# fig = px.area(df, x='Time', facet_col="channel", facet_col_wrap=10,
#               category_orders={"channel": sorted(df['channel'].unique())})
fig.update_layout(
    title="Dynamic Y-Axis Scaling for Each Channel",
    yaxis=dict(autorange=True)  # Ensures each facet gets its own range based on its data
)
fig.show()
