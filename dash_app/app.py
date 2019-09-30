# -*- coding: utf-8 -*-
import dash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

from db.api import get_processing_rate, get_latency, get_info_near

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

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
                                    'zoom': 7,
                                    'pitch': 0,
                                    'bearing':0,
                                    'center': {'lat':42.940, 'lon':-76.933}
                                    
                                },
                                'margin': {'l': 10, 'r':10, 'b':10, 't':30, 'pad':5},
                                'automargin': True
                            }
                        }
                    ),
                    style={'border': '1px solid gray'}
                ),
                html.Div('(42.940, -76.933)', id='coordinate-display', style={'align': 'right', 'padding': 10}),
            ])

        ]),
        dcc.Interval(
                id="update-ticker",
                interval=2000,
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
        return '({:.3f}, {:.3f})'.format(relayoutData['mapbox.center']['lat'], relayoutData['mapbox.center']['lon'])
    return old_val


@app.callback(
    Output('map-graph', 'figure'),
    [Input('map-graph', 'relayoutData'), Input('update-ticker', 'n_intervals')],
    [State('map-graph', 'figure')]
    )
def update_points(relayoutData, n_intervals, figure):    
    if relayoutData and 'mapbox.center' in relayoutData:
        lat = relayoutData['mapbox.center']['lat']
        lon = relayoutData['mapbox.center']['lon']
        mapbox = figure['layout']['mapbox']
        center = mapbox['center']
        center['lat'] = lat
        center['lon'] = lon
        mapbox['zoom'] = relayoutData['mapbox.zoom']
        mapbox['pitch'] = relayoutData['mapbox.pitch']
        mapbox['bearing'] = relayoutData['mapbox.bearing']
        figure['data'] = [get_info_near(lon, lat, 1000)]
    return figure


if __name__ == '__main__':
    app.run_server(debug=True)
