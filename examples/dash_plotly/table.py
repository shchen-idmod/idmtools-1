from dash import Dash, html, dash_table
import pandas as pd

# Sample data for the DataTable
df = pd.DataFrame({
    'City': ['NYC', 'Los Angeles', 'Chicago'],
    'Temperature': [59, 76, 48],
    'Humidity': [56, 22, 73]
})

app = Dash(__name__)

app.layout = html.Div([
    html.Div([
        dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            style_cell={'textAlign': 'center'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ]
        )
    ], className='custom-table')  # Apply the CSS class here
])

if __name__ == '__main__':
    app.run_server(debug=True)
