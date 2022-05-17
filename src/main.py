from pydoc import classname
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_extensions as de

from dash import Dash, html, dcc, Input, Output, State

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
races['date'] = races['date'].str[:6] + races['year'].astype(str)

# add date and constructor name to constructors standings
constructors_standings = pd.merge(constructors_standings, races[['date', 'raceId']], on=['raceId'], how='left')
constructors_standings = pd.merge(constructors_standings, constructors[['constructorId', 'name']], on=['constructorId'], how='left')

# clean up the data
df = constructors_standings
df['date'] = pd.to_datetime(df['date'], infer_datetime_format=True)
df = df.set_index('date')
df = df.loc['2010-01-01':'2022-12-31']
df = df[['name', 'position']]
df = df.groupby([pd.Grouper(freq="M"), 'name'])['position'].mean().reset_index()

# map configurations
map_fig = px.scatter_geo(circuits, lat="lat", lon="lng", hover_name="name",
                         projection="natural earth", hover_data=["country"])

# layout
app.layout = html.Div([
    html.Div(
        className="navigation-bar",
        children=[
            html.Img(className="logo", src=("https://www.formula1.com/etc/designs/fom-website/images/f1_logo.svg")),
            html.H2('F1 Data Visualization'),
            html.Div(className="lottie", children=[de.Lottie(options=lottie_options, url=lottie_url)])
            
        ]
    ),

    html.Div(
        className="info-box",
        children=[
            html.H4("Purpose of the application"),
            html.P(["The visualization aims to provide information about Formula 1, focusing on Contructors' "
                    "performance and Grand Prix races.",
                    html.Br(),
                    "In the application you can examine each Contructor's performance throughout "
                    "the years and monitor where different Grand Prix races have been organized.",
                    html.Br(),
                    "You can specify the years to examine, which then limits the observed set.",
                    html.Br(),
                    "By specifying the Grand Prix, you will see relevant information for that particular circuit.",
                    html.Br(),
                    "The visualization aims to answer a question I have wanted to to examine for awhile:",
                    html.Br(),
                    "'how have teams fared in the standings throughout the years and which teams "
                    "have performed the best in different Grand Prix races?'"
                ])
        ]
    ),

    html.Div(
        className="selector-box",
        children=[
            html.P("Select years to examine: "),
            dcc.Input(id='starting_year', type='number', min=1, max=2022, step=1, placeholder="From", value=2011),
            html.P(children=" -- "),
            dcc.Input(id='last_year', type='number', min=1, max=2022, step=1, placeholder="To", value=2022),
            html.P("Select circuit to examine: "),
            dcc.Dropdown(id = 'grand_prix', options = circuits.name, placeholder = "select a Grand Prix", value="Circuit de Monaco"),
        ]
    ),

    html.Div(
        className="graphs",
        children=[
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
                children=[
                    dcc.Graph(
                        id="map",
                        figure=map_fig
                    )
                ]
            )
        ]
    ),
])

# callback for graph
@app.callback(Output("graph", "figure"), Input("checklist", "value"), Input("starting_year", "value"), Input("last_year", "value"))
def update_line_chart(checklist, starting_year, last_year):

    df = constructors_standings
    df['date'] = pd.to_datetime(df['date'], infer_datetime_format=True)
    df = df.set_index('date')
    df = df.loc[f'{starting_year}-01-01':f'{last_year}-12-31']
    df = df[['name', 'position']]
    df = df.groupby([pd.Grouper(freq="M"), 'name'])['position'].mean().reset_index()

    mask = df['name'].isin(checklist)
    fig = px.line(df[mask], x="date", y="position", color='name')
    fig.update_layout(yaxis={'title': 'Constructor Standing',
                             'autorange': 'reversed'},
                      xaxis={'title': 'Year'})
    for x in range(starting_year, last_year):
        fig.add_vline(x=str(x), line_width=3, line_dash="dash", line_color="black")
    return fig

# callback for checklist
@app.callback(Output("checklist", "options"), Input("starting_year", "value"), Input("last_year", "value"))
def update_checklist(starting_year, last_year):
    df = constructors_standings
    df['date'] = pd.to_datetime(df['date'], infer_datetime_format=True)
    df = df.set_index('date')
    df = df.loc[f'{starting_year}-01-01':f'{last_year}-12-31']
    df = df[['name', 'position']]
    df = df.groupby([pd.Grouper(freq="M"), 'name'])['position'].mean().reset_index()

    return [{'label': x, 'value': x} for x in df.sort_values('name')['name'].unique()]

# callback for map
@app.callback(Output("map", "figure"), Input("grand_prix", "value"))
def center_map(grand_prix):
    lat = circuits.loc[circuits['name'] == grand_prix, 'lat'].item()
    lon = circuits.loc[circuits['name'] == grand_prix, 'lng'].item()
    return px.scatter_geo(circuits, lat="lat", lon="lng", hover_name="name",
                          projection="natural earth", hover_data=["country"],
                          center=dict(lat=lat, lon=lon))        

app.run_server(debug=True)