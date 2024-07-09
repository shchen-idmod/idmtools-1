from dash import Dash, html, dash_table
import pandas as pd

# Create a Dash application
app = Dash(__name__)

# Sample DataFrame to populate the DataTable
df = pd.DataFrame({
    'Description': ['Item 1', 'Item 2', 'Item 3'],
    'Details': [
        'Click [here](http://example.com)',
        '**Bold** text and _italic_',
        '`Code` snippet'
    ]
})

# Define the layout of the app
app.layout = html.Div([
    dash_table.DataTable(
        id='table',
        columns=[
            {"name": "Description", "id": "Description"},
            {"name": "Details", "id": "Details", "presentation": "markdown"}
        ],
        data=df.to_dict('records'),
        markdown_options={"link_target": "_blank"}  # Open links in new tabs
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
