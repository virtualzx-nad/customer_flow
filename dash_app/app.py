# -*- coding: utf-8 -*-
import time
import datetime

import numpy as np
import dash
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

from db_api.redis_connection import get_info_near, get_categories
from db_api.pulsar_connection import LatencyTracker, SourceController
from layout import get_layout 

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# initial coordinates for the map
lat0, lon0 = 36.107, -115.168 
zoom0 = 14
pitch0 = bearing0 = 0


# Connect to Pulsar to get the metrics data and controller for the source
latency_tracker = LatencyTracker()
source_controller = SourceController('checkin_controller')


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = get_layout(lat0, lon0, zoom0, pitch0, bearing0)


def create_latency_figure(max_len=60):
    """Create the average latency figure"""
    latency_tracker.update()
    keys = sorted(latency_tracker.time.keys())
    now = datetime.datetime.now()
    time_vals = [datetime.datetime.fromtimestamp(t)
                 for t in latency_tracker.time['all'][-max_len:]]
    latency = np.array(latency_tracker.latency['all'][-max_len:]) * 1e-3
    if latency.size:
        max_latency = np.max(latency)
    else:
        max_latency = 1
    return {
        'data': [go.Scatter(
                    x=time_vals,
                    y=latency,
                    mode='lines'
                )]
        ,
        'layout': {
            'height': 220,
            'margin': {'l': 70, 'b': 40, 'r': 10, 't': 10},
            'yaxis': {'type': 'linear', 'range': [0, max_latency], 'autorange': False, 'title': 'Latency (s)'},
            'xaxis': {'range': [now-datetime.timedelta(seconds=60), now], 'autorange': False, 'title': 'Date'}
        }
    }

def create_rate_figure(max_len=60):
    """Create the processing rate figure"""
    latency_tracker.update()
    keys = sorted(latency_tracker.time.keys())
    data = []
    now = datetime.datetime.now()
    i = 0
    for key in keys:
        time_vals = [datetime.datetime.fromtimestamp(t) for t in latency_tracker.time[key][-max_len:]]
        rate = latency_tracker.rate[key][-max_len:]
        if key == 'all':
            name = 'Total'
            style = {'width': 3, 'color': 'black'}
        else:
            name = 'Worker ' + str(i)
            style = {}
            i += 1
        data.append(go.Scatter(
                    x=time_vals,
                    y=rate,
                    line=style,
                    mode='lines',
                    name=name
                    ))
        if key == 'all':
            # Add ingestion rate data
            inrate = latency_tracker.ingestion_rate['all'][-max_len:]
            data.append(go.Scatter(x=time_vals, y=inrate, line={'width':2, 'color':'royalblue', 'dash': 'dash'},
                                   name='Ingestion', mode='lines'))
    return {
        'data': data 
        ,
        'layout': {
            'height': 220,
            'margin': {'l': 70, 'b': 40, 'r': 10, 't': 10},
            'yaxis': {'type': 'linear', 'range': [0,5], 'autorange': False, 'title': 'Rate (x1000msg/s)'},
            'xaxis': {'range': [now-datetime.timedelta(seconds=60), now], 'autorange': False, 'title': 'Date'},
            'legend':{'x':0.05,'y':0.95, 'borderwidth':1, 'bgcolor':'white' }
        }
    }

@app.callback(
    Output('latency-graph', 'figure'),
    [Input('update-ticker', 'n_intervals')]
    )
def update_latency(n_intervals):
    return create_latency_figure()

@app.callback(
    Output('rate-graph', 'figure'),
    [Input('update-ticker', 'n_intervals')]
    )
def update_rate(n_intervals):
    return create_rate_figure()

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
    df = get_info_near(lon, lat, 1000, latency_tracker.real_time, max_results=500, max_shown=500, category=category)
    figure['data'] = [go.Scattermapbox(lon=df['longitude'], lat=df['latitude'], text=df['label'],
                                       name='nearby_business', marker=dict(size=5, color=df['ratio'], colorscale='Jet',
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


@app.callback(
    Output('empty-div1', 'children'),
    [Input('ingestion-rate-input', 'value')]
    )
def update_ingestion_rate(rate):
    rate = max(1, int(rate))
    source_controller.set_max_rate(rate)
    return 'Max rate set to ' + str(rate)


@app.callback(
    Output('empty-div2', 'children'),
    [Input('multiplicity-input', 'value')]
    )
def update_multiplicity(multiplicity):
    multiplicity = max(1, int(multiplicity))
    source_controller.set_multiplicity(multiplicity)
    return 'Multiplicity set to ' + str(multiplicity)


@app.callback(
    Output('empty-div3', 'children'),
    [Input('partitions-input', 'value')]
    )
def update_partitions(partitions):
    partitions = max(1, int(partitions))
    source_controller.set_partition(partitions)
    return 'Partitions set to ' + str(partitions)


@app.callback(
    Output('empty-div4', 'children'),
    [Input('pause-button', 'n_clicks')]
    )
def pause_source(n_clicks):
    source_controller.pause()
    return 'Input source paused.'


@app.callback(
    Output('empty-div5', 'children'),
    [Input('resume-button', 'n_clicks')]
    )
def resume_source(n_clicks):
    source_controller.resume()
    return 'Input source resumed'


@app.callback(
    Output('realtime-div', 'children'),
    [Input('update-ticker', 'n_intervals')]
    )
def update_realtime(n_intervals):
    return str(datetime.datetime.fromtimestamp(latency_tracker.real_time))


if __name__ == '__main__':
    app.run_server(debug=True, port=8080, host='0.0.0.0')
