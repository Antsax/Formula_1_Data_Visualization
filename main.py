from pydoc import classname
import pandas as pd
import plotly.express as px
import dash_extensions as de

from dash import Dash, html, dcc, Input, Output

from src.lib.dataframe_helper import get_dataframes_from_directory

# setting up dash and dataframes
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
lottie_url = "https://assets8.lottiefiles.com/packages/lf20_lfuo4vnm.json"
lottie_options = dict(loop=False, renderSettings=dict(preserveAspectRatio='xMidYMid slice'))
dataframes = get_dataframes_from_directory('data')

app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# set up the dataframes
constructors = dataframes['constructors']
races = dataframes['races']
results = dataframes['results']
drivers = dataframes['drivers']
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

# set up dataframe for getting relevant information
results = results.drop(columns=['resultId', 'number', 'grid', 'position', 'positionText', 'positionOrder',
                                'points', 'laps', 'time', 'milliseconds', 'fastestLap', 'rank', 'fastestLapSpeed', 'statusId'])
results = pd.merge(results, drivers[['forename', 'surname', 'driverId']], on=['driverId'], how="left")
results = pd.merge(results, races[['year', 'circuitId', 'raceId']], on=['raceId'], how="left")
results = pd.merge(results, circuits[['name', 'circuitId']], on=['circuitId'], how="left")
results = pd.merge(results, constructors[['constructorId', 'name']], on=['constructorId'], how='left')
results = results[results['fastestLapTime'] != '\\N']
results['fastestLapTime'] = pd.to_datetime(results['fastestLapTime'], format="%M:%S.%f").dt.time

# create dataframe with best results
best_df = pd.DataFrame()
for circuitId in circuits['circuitId']:
    examined_set = results.loc[results['circuitId'] == circuitId]
    try:
        fastest_time= min(examined_set['fastestLapTime'])
        fastest_record = results.loc[results['fastestLapTime'] == fastest_time]
        fastest_record = fastest_record.drop(columns=['raceId', 'driverId', 'constructorId', 'circuitId'])
        best_df = pd.concat([best_df, fastest_record], ignore_index = True)
    except ValueError:
        circuit_name = circuits.loc[circuits['circuitId'] == circuitId, 'name'].item()
        replace_set = pd.DataFrame({'fastestLapTime': ['NA'], 'forename': ['NA'], 'surname': ['NA'],  'year': ['NA'], 'name_x': [circuit_name], 'name_y': ['NA']})
        best_df = pd.concat([best_df, replace_set], ignore_index = True)

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
                    "have performed the best in different Grand Prix races?'",
                    html.Br(),
                    html.Br(),
                    html.B("NOTE: the application is extremely slow, so please do not take too ambitious leaps in examined timeframe")
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

    html.Div(
        className="best_performer",
        children=[
            html.H3("Best performance in given circuit"),
            html.Div(
                id='lap_div',
                children=[
                    html.H5("Lap time"),
                    html.P(
                        id="lap_time"
                    )
                ]
            ),

            html.Div(
                id='driver_div',
                children=[
                    html.H5("Driver"),
                    html.P(
                        id="driver"
                    )
                ]
            ),

            html.Div(
                id='year_div',
                children=[
                    html.H5("Year"),
                    html.P(
                        id="year"
                    )
                ]
            ),

            html.Div(
                id='team_div',
                children=[
                    html.H5("Constructor"),
                    html.P(
                        id="team"
                    )
                ]
            ),
        ]
    )
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

# callback for lap time
@app.callback(Output("lap_time", "children"), Input("grand_prix", "value"))
def get_lap_time(grand_prix):
    lap_time = str(best_df.loc[best_df['name_x'] == grand_prix, 'fastestLapTime'].item())
    if lap_time == 'NA':
        return "NA"
    return lap_time[3:12]

# callback for driver
@app.callback(Output("driver", "children"), Input("grand_prix", "value"))
def get_driver(grand_prix):
    first_name = str(best_df.loc[best_df['name_x'] == grand_prix, 'forename'].item())
    last_name = str(best_df.loc[best_df['name_x'] == grand_prix, 'surname'].item())
    if first_name == 'NA':
        return "NA"
    return f'{first_name} {last_name}'

# callback for year
@app.callback(Output("year", "children"), Input("grand_prix", "value"))
def get_year(grand_prix):
    year = str(best_df.loc[best_df['name_x'] == grand_prix, 'year'].item())
    if year == 'NA':
        return "NA"
    return year

# callback for constructor
@app.callback(Output("team", "children"), Input("grand_prix", "value"))
def get_team(grand_prix):
    team = str(best_df.loc[best_df['name_x'] == grand_prix, 'name_y'].item())
    if team == 'NA':
        return "NA"
    return team
     

if __name__ == '__main__':
    app.run_server()