from collections import namedtuple
import os
import pathlib

import bokeh.io
import bokeh.layouts as layouts
import bokeh.models as models
import bokeh.plotting as plotting
import click
import pandas as pd


PLOT_WIDTH = 700
PLOT_HEIGHT = 300
TOOLS = 'pan,xwheel_pan,box_zoom,reset,save'
linedesc = namedtuple("linedesc", ['col', 'legend', 'color'])


class IsNotCSVFile(Exception):
    pass


def create_plot(title, ylabel, source, lines, yformatter=None):
    fig = plotting.figure(
        plot_width=PLOT_WIDTH,
        plot_height=PLOT_HEIGHT,
        tools=TOOLS
    )
    fig.title.text = title
    fig.xaxis.axis_label = 'Time (s)'
    fig.yaxis.axis_label = ylabel

    fig.xaxis.formatter = models.NumeralTickFormatter(format='0,0.00')
    if yformatter is not None:
        fig.yaxis.formatter = yformatter

    is_legend = False
    for x in lines:
        if x.legend != '':
            is_legend = True
            fig.line(x='sTime', y=x.col, color=x.color, legend_label=x.legend, source=source)
        else:
            fig.line(x='sTime', y=x.col, color=x.color, source=source)

    if is_legend:
        fig.legend.click_policy="hide"

    return fig


def create_packets_plot_snd(source, is_total):
    type = 'Total' if is_total else 'Instant'

    if is_total:
        lines = [
            linedesc('pktSentTotal', 'Sent', 'green'),
            linedesc('pktLostTotal', 'Lost', 'red'),
        ]
    else:
        lines = [
            linedesc('pktSent', 'Sent', 'green'),
            linedesc('pktLost', 'Lost', 'red'),
        ]

    return create_plot(
        f'Packets (Sender Side), {type}',
        'Number of Packets',
        source,
        lines,
        models.NumeralTickFormatter(format='0,0')
    )


def create_packets_plot_rcv(source, is_total):
    type = 'Total' if is_total else 'Instant'

    if is_total:
        lines = [
            linedesc('pktRecvTotal', 'Received', 'green'),
            linedesc('pktDecryptFailTotal', 'Decryption Failed', 'red')
        ]
    else:
        lines = [
            linedesc('pktRecv', 'Received', 'green'),
            linedesc('pktDecryptFail', 'Decryption Failed', 'red')
        ]

    return create_plot(
        f'Packets (Receiver Side), {type}',
        'Number of Packets',
        source,
        lines,
        models.NumeralTickFormatter(format='0,0')
    )


def create_acks_plot(source, is_total):
    type = 'Total' if is_total else 'Instant'

    if is_total:
        lines = [
            linedesc('pktRecvAck', 'Received Acks', 'orange'),
            linedesc('pktRecvLateAck', 'Received Late Acks', 'blue')
        ]
    else:
        lines = [
            # linedesc('pktSent', 'Sent', 'green'),
            # linedesc('pktLost', 'Lost', 'red'),
        ]

    return create_plot(
        f'Acknowledgment Packets (Sender Side), {type}',
        'Number of Packets',
        source,
        lines,
        models.NumeralTickFormatter(format='0,0')
    )


def create_bytes_plot_rcv(source, is_total):
    type = 'Total' if is_total else 'Instant'

    if is_total:
        lines = [linedesc('bytesRecvTotal', '', 'green')]
    else:
        lines = [linedesc('bytesRecv', '', 'green')]

    return create_plot(
        f'Bytes Received (Receiver Side), {type}',
        'Bytes',
        source,
        lines,
        models.NumeralTickFormatter(format='0,0')
    )


def calculate_instant_stats(df: pd.DataFrame):
    df['pktSent'] = df['pktSentTotal'].diff().fillna(df['pktSentTotal'].iloc[0]).astype('int32')
    df['pktLost'] = df['pktLostTotal'].diff().fillna(df['pktLostTotal'].iloc[0]).astype('int32')

    df['pktRecv'] = df['pktRecvTotal'].diff().fillna(df['pktRecvTotal'].iloc[0]).astype('int32')
    df['pktDecryptFail'] = df['pktDecryptFailTotal'].diff().fillna(df['pktDecryptFailTotal'].iloc[0]).astype('int32')
    df['bytesRecv'] = df['bytesRecvTotal'].diff().fillna(df['bytesRecvTotal'].iloc[0])

    return df[[
        'Timepoint', 'Time', 'sTime',
        'pktSent', 'pktSentTotal', 'pktLost', 'pktLostTotal',               # sender side
        'pktRecvAck', 'pktRecvLateAck',                                     # sender side
        'pktRecv', 'pktRecvTotal', 'pktDecryptFail', 'pktDecryptFailTotal', # receiver side
        'bytesRecv', 'bytesRecvTotal',                                      # receiver side
    ]]


@click.command()
@click.argument(
    'stats_filepath',
    type=click.Path(exists=True)
)
def plot_graph(stats_filepath):
    """
    This script processes .csv file with SRT over QUIC statistics produced by
    test application and visualizes the data.
    """
    filepath = pathlib.Path(stats_filepath)
    filename = filepath.name

    if not filename.endswith('.csv'):
        raise IsNotCSVFile(f'{filepath} does not correspond to a .csv file')

    name, _ = filename.rsplit('.', 1)
    name_parts = name.split('-')
    html_filename = name + '.html'
    html_filepath = filepath.parent / html_filename

    # Prepare data
    df = pd.read_csv(filepath)

    print(df)
    print(df.info())

    df['Timepoint'] = pd.to_datetime(df['Timepoint'])
    df['Time'] = df['Timepoint'] - df['Timepoint'].iloc[0]
    df['sTime'] = df['Time'].dt.total_seconds()
    df = calculate_instant_stats(df)

    print(df)
    print(df.info())

    source = models.ColumnDataSource(df)

    # Output to static .html file
    plotting.output_file(html_filepath, title="SRT Stats Visualization")

    # A dict for storing plots
    plots = {}

    # Create plots

    # Packets statistics
    plots['packets_snd_total'] = create_packets_plot_snd(source, True)
    plots['packets_snd_instant'] = create_packets_plot_snd(source, False)
    plots['packets_rcv_total'] = create_packets_plot_rcv(source, True)
    plots['packets_rcv_instant'] = create_packets_plot_rcv(source, False)

    # Acknowledgement packets statistics
    plots['acks_total'] = create_acks_plot(source, True)

    # Statistics in bytes
    plots['bytes_rcv_total'] = create_bytes_plot_rcv(source, True)
    plots['bytes_rcv_instant'] = create_bytes_plot_rcv(source, False)

    # Syncronize x-ranges of figures
    last_key = list(plots)[-1]
    last_fig = plots[last_key]
    
    for fig in plots.values():
        if fig is None:
            continue
        fig.x_range = last_fig.x_range

    # Show the results
    grid = layouts.gridplot(
        [
            [plots['packets_snd_instant'], plots['packets_snd_total']],
            [None, plots['acks_total']],
            [plots['packets_rcv_instant'], plots['packets_rcv_total']],
            [plots['bytes_rcv_instant'], plots['bytes_rcv_total']]
        ]
    )
    plotting.show(grid)


if __name__ == '__main__':
    plot_graph()
