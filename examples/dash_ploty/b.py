from dash import Dash, html, dcc, Input, Output, callback

app = Dash(__name__)
experiments = [
    {'id': 'exp1', 'name': 'Experiment 1', 'description': 'This is the first experiment.'},
    {'id': 'exp2', 'name': 'Experiment 2', 'description': 'This is the second experiment.'}
]

simulations = [
    {'id': 'sim1', 'exp_id': 'exp1', 'status': 'Completed'},
    {'id': 'sim2', 'exp_id': 'exp1', 'status': 'Running'},
    {'id': 'sim3', 'exp_id': 'exp2', 'status': 'Failed'}
]

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.H1('Research Dashboard'),
    html.Div(id='page-content')
])

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == "/" or pathname == "/experiments":
        return html.Div([
            html.H2('Experiments'),
            html.Ul([
                html.Li(html.A(exp['name'], href=f'/simulations/{exp["id"]}'))
                for exp in experiments
            ])
        ])
    elif '/simulations' in pathname:
        exp_id = pathname.split('/')[-1]
        relevant_sims = [sim for sim in simulations if sim['exp_id'] == exp_id]
        return html.Div([
            html.H2(f'Simulations for Experiment ID {exp_id}'),
            html.Ul([html.Li(f'ID: {sim["id"]}, Status: {sim["status"]}') for sim in relevant_sims])
        ])
    return '404'

if __name__ == '__main__':
    app.run_server(debug=True, port="8051")
