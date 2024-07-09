import dash
from dash import html, dcc
from dash.dash_table import DataTable
from dash.dependencies import Input, Output
import pandas as pd

# Sample data
data = pd.DataFrame({
    'Product': ['Apple', 'Banana', 'Cherry'],
    'Sales': [300, 150, 400],
    'Profit': [90, 40, 120],
    'Customer Ratings': [4.5, 4.0, 3.8]
})

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Checklist(
        id='column-selector',
        options=[{'label': col, 'value': col} for col in data.columns],
        value=['Product', 'Sales', 'Profit'],  # Default selected columns
        inline=True
    ),
    DataTable(
        id='table',
        data=data.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in data.columns if col in ['Product', 'Sales', 'Profit']]  # Initial columns
    )
])

@app.callback(
    Output('table', 'columns'),
    [Input('column-selector', 'value')]
)
def update_columns(selected_columns):
    return [{'name': col, 'id': col} for col in selected_columns]

if __name__ == '__main__':
    app.run_server(debug=True, port="8051")
