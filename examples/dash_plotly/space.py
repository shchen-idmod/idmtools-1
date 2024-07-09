from dash import Dash, html, dcc

app = Dash(__name__)

# app.layout = html.Div([
#     html.Div('This is the first text block.', style={'margin': '10px', 'padding': '20px'}),
#     html.Div('This is the second text block.', style={'margin': '20px', 'padding': '30px', 'backgroundColor': 'lightblue'})
# ])
app.layout = html.Div([
    html.Div('This is the first text block.', className='content-block'),
    html.Div('', className='spacer'),  # This acts as a spacer
    html.Div('This is the second text block.', className='content-block')
])

if __name__ == '__main__':
    app.run_server(debug=True)
# app.layout = html.Div([
#     html.Div('This is the first text block.', className='content-block'),
#     html.Div('', className='spacer'),  # This acts as a spacer
#     html.Div('This is the second text block.', className='content-block')
# ])
