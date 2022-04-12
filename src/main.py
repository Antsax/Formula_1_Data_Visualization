import pandas as pd
import plotly.express as px

from dash import Dash, html, dcc, Input, Output
from pathlib import Path

from lib.dataframe_helper import get_dataframes_from_directory

# setting up dash and dataframes
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets)
dataframes = get_dataframes_from_directory('data')

# set up the dataframes
constructors = dataframes['constructors']
races = dataframes['races']
constructors_standings = dataframes['constructor_standings']

# add date and constructor name to constructors standings
constructors_standings = pd.merge(constructors_standings, races[['date', 'raceId']], on=['raceId'], how='left')
constructors_standings = pd.merge(constructors_standings, constructors[['constructorId', 'name']], on=['constructorId'], how='left')

# clean up the data
df = constructors_standings
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date')
df = df.loc['2010-01-01':'2022-12-31']
df = df[['name', 'position']]
df = df.groupby([pd.Grouper(freq="M"),'name'])['position'].mean().reset_index()
# print(df)

# layout
app.layout = html.Div([
    html.H4('Constructors standings by year'),
    dcc.Graph(id="graph"),
    dcc.Checklist(
        id="checklist",
        options=["Mercedes", "Ferrari", "Red Bull", "McLaren", "Alpine F1 Team", "Alfa Romeo", "Haas F1 Team", "AlphaTauri", "Williams", "Aston Martin"],
        #options=[{'label': x, 'value': x} for x in df.sort_values('name')['name'].unique()],
        value=["Mercedes", "Ferrari", "Red Bull", "McLaren", "Alpine"],
        inline=True
    ),
])

# callback
@app.callback(Output("graph", "figure"), Input("checklist", "value"))
def update_line_chart(constructors):
    mask = df['name'].isin(constructors)
    fig = px.line(df[mask], x="date", y="position", color='name')
    fig.update_layout(yaxis={'title': 'Constructor Standing',
                             'autorange': 'reversed'},
                      xaxis={'title': 'Year'})
    return fig

app.run_server(debug=True)