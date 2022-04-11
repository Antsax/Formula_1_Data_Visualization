import pandas as pd
import plotly.express as px

from dash import Dash, html, dcc, Input, Output
from pathlib import Path

from lib.dataframe_helper import get_dataframes_from_directory


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)

dataframes = get_dataframes_from_directory('data')

constructors = dataframes['constructors']

df = dataframes['constructors_standings']

app.layout = html.Div([
    html.H4('Constructors standings by year'),
    dcc.Graph(id="graph"),
    dcc.Checklist(
        id="checklist",
        options=["Mercedes", "Ferrari", "Red Bull Racing", "McLaren", "Alpine", "Alfa Romeo", "Haas", "Alphatauri", "Williams", "Aston Martin"],
        value=["Mercedes", "Ferrari", "Red Bull Racing", "McLaren", "Alpine"],
        inline=True
    ),
])


@app.callback(Output("graph", "figure"), Input("checklist", "value"))
def update_line_chart(constructors):
    df = dataframes['constructors_standings']
    mask = df.constructorId.isin(constructors)
    fig = px.line(df[mask], 
        x="Year", y="Standing", color='Constructor')
    return fig

app.run_server(debug=True)