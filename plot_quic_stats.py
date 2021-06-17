from collections import namedtuple
import pathlib

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
        f'Packets, {type}',
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
        f'Packets, {type}',
        'Number of Packets',
        source,
        lines,
        models.NumeralTickFormatter(format='0,0')
    )


def create_acks_plot(source, is_total):
    type = 'Total' if is_total else 'Instant'

    if is_total:
        lines = [
            linedesc('pktRecvAckTotal', 'Acks', 'orange'),
            linedesc('pktRecvLateAckTotal', 'Late Acks', 'blue')
        ]
    else:
        lines = [
            linedesc('pktRecvAck', 'Acks', 'orange'),
            linedesc('pktRecvLateAck', 'Late Acks', 'blue')
        ]

    return create_plot(
        f'Acknowledgments Received, {type}',
        'Number of Packets',
        source,
        lines,
        models.NumeralTickFormatter(format='0,0')
    )


def create_bytes_plot(source, is_snd, is_total):
    type = 'Total' if is_total else 'Instant'
    side = 'Sent' if is_snd else 'Recv'
    title = f'Bytes Sent, {type}' if is_snd else f'Bytes Received, {type}'

    if is_total:
        lines = [linedesc(f'bytes{side}Total', '', 'green')]
    else:
        lines = [linedesc(f'bytes{side}', '', 'green')]

    return create_plot(
        title,
        'Bytes',
        source,
        lines,
        models.NumeralTickFormatter(format='0,0')
    )


def create_megabits_plot(source, is_snd, is_total):
    # These graphs are correct if only statistics are collected each 1s
    type = 'Total' if is_total else 'Instant'
    side = 'Sent' if is_snd else 'Recv'
    title = f'Megabits Sent, {type}' if is_snd else f'Megabits Received, {type}'

    if is_total:
        lines = [linedesc(f'megabits{side}Total', '', 'green')]
    else:
        lines = [linedesc(f'megabits{side}', '', 'green')]

    return create_plot(
        title,
        'Megabits',
        source,
        lines,
        models.NumeralTickFormatter(format='0,0.00')
    )


def create_rtt_plot(source):
    lines = [linedesc('msRTTSmoothed', '', 'blue')]

    return create_plot(
        'Smoothed RTT',
        'Milliseconds (ms)',
        source,
        lines
    )


def panel(source, is_snd):
    side = 'Sender' if is_snd else 'Receiver'

    plots = {}

    if is_snd:
        plots['packets_total'] = create_packets_plot_snd(source, True)
        plots['packets_instant'] = create_packets_plot_snd(source, False)
        plots['acks_total'] = create_acks_plot(source, True)
        plots['rtt'] = create_rtt_plot(source)
    else:
        plots['packets_total'] = create_packets_plot_rcv(source, True)
        plots['packets_instant'] = create_packets_plot_rcv(source, False)
        plots['acks_total'] = None
        plots['rtt'] = None

    plots['bytes_total'] = create_bytes_plot(source, is_snd, True)
    plots['bytes_instant'] = create_bytes_plot(source, is_snd, False)
    plots['megabits_total'] = create_megabits_plot(source, is_snd, True)
    plots['megabits_instant'] = create_megabits_plot(source, is_snd, False)

    # Syncronize x-ranges of figures
    last_key = list(plots)[-1]
    last_fig = plots[last_key]
    
    for fig in plots.values():
        if fig is None:
            continue
        fig.x_range = last_fig.x_range

    grid = layouts.gridplot(
        [
            [plots['packets_instant'], plots['packets_total']],
            [plots['bytes_instant'], plots['bytes_total']],
            [plots['megabits_instant'], plots['megabits_total']],
            [None, plots['acks_total']],
            [plots['rtt'], None],
        ]
    )

    panel = models.widgets.Panel(child=grid, title=f'{side} Statistics')
    return panel


def calculate_instant_stats(df: pd.DataFrame):
    df['pktSent'] = df['pktSentTotal'].diff().fillna(df['pktSentTotal'].iloc[0]).astype('int32')
    df['pktLost'] = df['pktLostTotal'].diff().fillna(df['pktLostTotal'].iloc[0]).astype('int32')
    df['bytesSent'] = df['bytesSentTotal'].diff().fillna(df['bytesSentTotal'].iloc[0])
    df['megabitsSentTotal'] = df['bytesSentTotal'] * 8 / 1000000
    df['megabitsSent'] = df['megabitsSentTotal'].diff().fillna(df['megabitsSentTotal'].iloc[0])
    df['pktRecvAck'] = df['pktRecvAckTotal'].diff().fillna(df['pktRecvAckTotal'].iloc[0]).astype('int32')
    df['pktRecvLateAck'] = df['pktRecvLateAckTotal'].diff().fillna(df['pktRecvLateAckTotal'].iloc[0]).astype('int32')

    df['pktRecv'] = df['pktRecvTotal'].diff().fillna(df['pktRecvTotal'].iloc[0]).astype('int32')
    df['pktDecryptFail'] = df['pktDecryptFailTotal'].diff().fillna(df['pktDecryptFailTotal'].iloc[0]).astype('int32')
    df['bytesRecv'] = df['bytesRecvTotal'].diff().fillna(df['bytesRecvTotal'].iloc[0])
    df['megabitsRecvTotal'] = df['bytesRecvTotal'] * 8 / 1000000
    df['megabitsRecv'] = df['megabitsRecvTotal'].diff().fillna(df['megabitsRecvTotal'].iloc[0])

    return df[[
        'Timepoint', 'Time', 'sTime',
        'pktSent', 'pktSentTotal', 'pktLost', 'pktLostTotal',                          # sender side
        'bytesSent', 'bytesSentTotal', 'megabitsSent', 'megabitsSentTotal',            # sender side
        'pktRecvAck', 'pktRecvLateAckTotal','pktRecvAckTotal', 'pktRecvLateAckTotal',  # sender side
        'msRTTSmoothed',                                                               # sender side
        'pktRecv', 'pktRecvTotal', 'pktDecryptFail', 'pktDecryptFailTotal',            # receiver side
        'bytesRecv', 'bytesRecvTotal', 'megabitsRecv', 'megabitsRecvTotal',            # receiver side
    ]]


@click.command()
@click.argument(
    'stats_filepath',
    type=click.Path(exists=True)
)
def main(stats_filepath):
    """
    This script processes .csv file with SRT over QUIC statistics produced by
    the test application and visualizes the data.
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
    df['Timepoint'] = pd.to_datetime(df['Timepoint'])
    df['Time'] = df['Timepoint'] - df['Timepoint'].iloc[0]
    df['sTime'] = df['Time'].dt.total_seconds()
    df = calculate_instant_stats(df)

    # Output to static .html file
    plotting.output_file(html_filepath, title="SRT over QUIC Statistics")
    panels = []

    source = models.ColumnDataSource(df)
    panels.append(panel(source, True))
    panels.append(panel(source, False))

    tabs = models.widgets.Tabs(tabs=panels)
    plotting.show(tabs)


if __name__ == '__main__':
    main()
