import dash
import dash_bootstrap_components as dbc
from dash import dcc, dash_table, html
from dash.dependencies import Input, Output, State
import base64
import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

app.layout = dbc.Container(
    [
        dcc.Store(id='uploaded-data', storage_type='memory'),  # Store for uploaded data
        html.H4(
            "Hierarchical Visualization",
            style={"textAlign": "center", "marginBottom": "25px", "marginTop": "25px", "fontSize": "32px"},
        ),
        dcc.Tabs(
            id="tab",
            value="upload",
            children=[
                dcc.Tab(label="Upload", value="upload"),
                dcc.Tab(label="KPI Tree", value="kpitree"),
                dcc.Tab(label="Sunburst", value="sunburst"),
            ],
            colors={"border": "white", "primary": "gray", "background": "lightgray"}
        ),
        html.Div(id="tabs-content", style={"marginTop": "25px"}),
    ],
    fluid=True,
)

def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    df = df.fillna('')
    return df[['Segment', 'parent']]

@app.callback(
    Output('tabs-content', 'children'),
    [Input('tab', 'value'),
     Input('uploaded-data', 'data')]
)
def main_callback_logic(tab, data):
    if data is None:
        if tab == "upload":
            return dbc.Row(
                dbc.Col([
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div(['Drag and Drop or ', html.A('Select a CSV File')]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px'
                        },
                        multiple=False
                    ),
                    html.Div(id='output-data-upload'),
                ], width=8),
                justify="center"
            )
        else:
            raise dash.exceptions.PreventUpdate("No data available.")

    df = pd.DataFrame(data)
    if tab == "upload":
        return html.Div([
            dcc.Graph(
                figure={
                    'data': [{'type': 'table',
                              'header': {'values': df.columns, 'fill': {'color': '#fafafa'}},
                              'cells': {'values': [df[col] for col in df.columns]}}
                             ],
                    'layout': {}
                }
            )
        ])

    elif tab == "kpitree":
        fig = go.Figure(go.Icicle(
            labels=df['Segment'],
            parents=df['parent'],
            tiling=dict(orientation='v')
        ))

    else:  # sunburst
        fig = go.Figure(go.Sunburst(
            labels=df['Segment'],
            parents=df['parent']
        ))

    fig.update_traces(root_color="lightgrey")
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    return dcc.Graph(figure=fig)

@app.callback(
    [Output('output-data-upload', 'children'),
     Output('uploaded-data', 'data')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_output(contents, filename):
    if contents is None:
        return dash.no_update

    df = parse_contents(contents)
    columns = [{'name': i, 'id': i} for i in df.columns]
    data = df.to_dict('records')

    table = dash_table.DataTable(data=data, columns=columns)

    return table, data

if __name__ == "__main__":
    app.run_server(debug=True)
