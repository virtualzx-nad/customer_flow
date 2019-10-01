# -*- coding: utf-8 -*-
from waitress import serve
import dash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

from db.api import get_processing_rate, get_latency, get_info_near, get_categories

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# initial coordinates for the map
lat0, lon0 = 43.126, -77.946
zoom0 = 5
pitch0 = bearing0 = 0

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H1('Hello Dash'),

    html.Div("Dash: A web application framework for Python."),

    html.Div(children=[

            html.Div(style={'width':'45%', 'display': 'inline-block'}, children=[
                html.Div("LeftPanel"),
                html.Div([
                    html.Div(style={'width':'48%', 'display': 'inline-block'}, children=
                        daq.Gauge(id='rate-meter', showCurrentValue=True, units='×1000',label='Processing Rate',
                        min=0, max=10, value=6.7, size=180)
                    ), 
                    html.Div(style={'width':'48%', 'display': 'inline-block'}, children=
                        daq.Gauge(id='latency-meter', showCurrentValue=True, units='microsecond',label='Latency',
                        min=0, max=1000, value=30, size=180)
                    )
                ])
            ]),
            html.Div(style={'width':'45%', 'display': 'inline-block'}, children=[
                html.Div(
                    dcc.Graph(
                        id='map-graph',
                        figure={
                            'data': [
                                {'type': 'scattermapbox', 'name': 'main-map'},
                            ],
                            'layout': {
                                'mapbox':{
                                    'style':  'light',
                                    'accesstoken': 'pk.eyJ1IjoidmlydHVhbHp4IiwiYSI6ImNrMTRra2s3ZDBsOTgzY3FkOG1ybnlodHQifQ.ggJkoaS_tOG6cPxB7BZ88w',
                                    'zoom': zoom0,
                                    'pitch': pitch0,
                                    'bearing':bearing0,
                                    'center': {'lat': lat0, 'lon': lon0}
                                    
                                },
                                'margin': {'l': 10, 'r':10, 'b':10, 't':30, 'pad':5},
                                'automargin': True
                            }
                        }
                    ),
                    style={'border': '1px solid gray'}
                ),
                html.Div([
                    html.Div('Coord ({:.3f}, {:.3f})'.format(lat0, lon0), id='coordinate-display', 
                             style={'width': '35%', 'align': 'left', 'padding': 0, 'display': 'inline-block'}),
                    html.Div('  Category',
                             style={'width':'15%', 'align': 'right', 'padding': 0, 'display': 'inline-block'}),
                    html.Div(style={'width':'37%', 'align': 'left', 'padding': 0, 'display': 'inline-block'},
                            children=dcc.Dropdown(id='category-dropdown',
                                 options=[{'label': 'Restaurants', 'value': 'geo:Restaurants'}],
                                 value='geo:Restaurants')
                            )
                ])
            ])

        ]),
        dcc.Interval(
                id="update-ticker",
                interval=5000,
                n_intervals=0,
            ),
])

@app.callback(
    Output('rate-meter', 'value'),
    [Input('update-ticker', 'n_intervals')]
    )
def update_rate(interval):
    return get_processing_rate()


@app.callback(
    Output('latency-meter', 'value'),
    [Input('update-ticker', 'n_intervals')]
    )
def update_latency(interval):
    return get_latency()


@app.callback(
    Output('coordinate-display', 'children'),
    [Input('map-graph', 'relayoutData')],
    [State('coordinate-display', 'children')]
    )
def update_latitude(relayoutData, old_val):    
    if relayoutData and 'mapbox.center' in relayoutData:
        return 'Coord ({:.3f}, {:.3f})'.format(relayoutData['mapbox.center']['lat'], relayoutData['mapbox.center']['lon'])
    return old_val


@app.callback(
    Output('map-graph', 'figure'),
    [Input('map-graph', 'relayoutData'), Input('update-ticker', 'n_intervals'), Input('category-dropdown', 'value')],
    [State('map-graph', 'figure')]
    )
def update_points(relayoutData, n_intervals, category, figure):    
    if relayoutData and 'mapbox.center' in relayoutData:
        lat = relayoutData['mapbox.center']['lat']
        lon = relayoutData['mapbox.center']['lon']
        zoom = relayoutData['mapbox.zoom']
        pitch = relayoutData['mapbox.pitch']
        bearing = relayoutData['mapbox.bearing']
    else:
        lat = lat0
        lon = lon0
        zoom = zoom0
        pitch = pitch0
        bearing = bearing0
    mapbox = figure['layout']['mapbox']
    center = mapbox['center']
    center['lat'] = lat
    center['lon'] = lon
    mapbox['zoom'] = zoom 
    mapbox['pitch'] = pitch 
    mapbox['bearing'] = bearing 
    df = get_info_near(lon, lat, 500, max_results=50000, max_shown=2000, category=category)
    figure['data'] = [go.Scattermapbox(lon=df['longitude'], lat=df['latitude'], text=df['label'],
                                       name='nearby_business', marker=dict(size=df['size'], color=df['ratio'], colorscale='Jet',
                                       showscale=True, cmax=1.0, cmin=0.0)
                      )]
    return figure


@app.callback(
    Output('category-dropdown', 'options'),
    [Input('update-ticker', 'n_intervals')]
    )
def update_category_dropdown(n_intervals):
    return [{'label': key, 'value': value}
            for key, value in sorted(get_categories().items())]


if __name__ == '__main__':
    app.run_server(debug=True, port=8080, host='0.0.0.0')
