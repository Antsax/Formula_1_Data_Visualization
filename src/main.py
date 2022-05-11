from pydoc import classname
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_extensions as de

from dash import Dash, html, dcc, Input, Output

from lib.dataframe_helper import get_dataframes_from_directory

# setting up dash and dataframes
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
lottie_url = "https://assets8.lottiefiles.com/packages/lf20_lfuo4vnm.json"
lottie_options = dict(loop=False, renderSettings=dict(preserveAspectRatio='xMidYMid slice'))
app = Dash(__name__, external_stylesheets=external_stylesheets)
dataframes = get_dataframes_from_directory('data')

# set up the dataframes
constructors = dataframes['constructors']
races = dataframes['races']
constructors_standings = dataframes['constructor_standings']
circuits = dataframes['circuits']

# add date and constructor name to constructors standings
constructors_standings = pd.merge(constructors_standings, races[['date', 'raceId']], on=['raceId'], how='left')
constructors_standings = pd.merge(constructors_standings, constructors[['constructorId', 'name']], on=['constructorId'], how='left')

# clean up the data
df = constructors_standings
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date')
df = df.loc['2010-01-01':'2022-12-31']
df = df[['name', 'position']]
df = df.groupby([pd.Grouper(freq="M"), 'name'])['position'].mean().reset_index()

# map configurations
map = circuits
map_fig = px.scatter_geo(map, lat="lat", lon="lng", hover_name="name",
                         projection="natural earth", hover_data=["country"])

# layout
app.layout = html.Div([
    html.Div(
        className="navigation-bar",
        children=[
            de.Lottie(options=lottie_options, width="5%", height="5%", url=lottie_url),
            html.H4('F1 DATA VISUALIZATION')]
    ),
    html.Div(
        className="constructors-graph",
        children=[
            dcc.Graph(id="graph"),
            dcc.Checklist(
                id="checklist",
                options=[{'label': x, 'value': x} for x in df.sort_values('name')['name'].unique()],
                value=["Mercedes", "Ferrari", "Red Bull", "McLaren", "Alpine"],
                inline=True
            )
        ]
    ),
    html.Div(
        className="map-graph",
        children=[dcc.Graph(id="map", figure=map_fig)]
    )
])

# callback for graph
@app.callback(Output("graph", "figure"), Input("checklist", "value"))
def update_line_chart(constructors):
    mask = df['name'].isin(constructors)
    fig = px.line(df[mask], x="date", y="position", color='name')
    fig.update_layout(yaxis={'title': 'Constructor Standing',
                             'autorange': 'reversed'},
                      xaxis={'title': 'Year'})
    for x in range(2011, 2023):
        fig.add_vline(x=str(x), line_width=3, line_dash="dash", line_color="black")
    return fig

app.run_server(debug=True)