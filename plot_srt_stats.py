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


def export_plot_png(export_png, plot, name, postfix):
    if export_png:
        # The following two lines remove toolbar from PNG
        plot.toolbar.logo = None
        plot.toolbar_location = None
        bokeh.io.export_png(plot, filename=f'{name}-{postfix}.png')


def create_plot(title, xlabel, ylabel, source, lines, yformatter=None):
    fig = plotting.figure(
        plot_width=PLOT_WIDTH,
        plot_height=PLOT_HEIGHT,
        tools=TOOLS
    )
    fig.title.text = title
    fig.xaxis.axis_label = xlabel
    fig.yaxis.axis_label = ylabel

    fig.xaxis.formatter = models.NumeralTickFormatter(format='0,0')
    if yformatter is not None:
        fig.yaxis.formatter = yformatter

    is_legend = False
    for x in lines:
        if x.legend != '':
            is_legend = True
            fig.line(x='Time', y=x.col, color=x.color, legend_label=x.legend, source=source)
        else:
            fig.line(x='Time', y=x.col, color=x.color, source=source)

    if is_legend:
        fig.legend.click_policy="hide"

    return fig


def create_packets_plot(source, is_sender):
    side_name = 'Sender' if is_sender else 'Receiver'

    if is_sender:
        lines = [
            linedesc('pktSent', 'Sent', 'green'),
            linedesc('pktSndLoss', 'Lost', 'orange'),
            linedesc('pktRetrans', 'Retransmitted', 'blue'),
            linedesc('pktSndDrop', 'Dropped', 'red'),
            linedesc('pktFlightSize', 'On Flight', 'black'),
        ]
    else:
        lines = [
            linedesc('pktRecv', 'Received', 'green'),
            linedesc('pktRcvLoss', 'Lost', 'orange'),
            linedesc('pktRcvRetrans', 'Retransmitted', 'blue'),
            linedesc('pktRcvBelated', 'Belated', 'grey'),
            linedesc('pktRcvDrop', 'Dropped', 'red'),
        ]

    return create_plot(
        'Packets (' + side_name + ' Side)',
        'Time (ms)',
        'Number of Packets',
        source,
        lines,
        models.NumeralTickFormatter(format='0,0')
    )


def create_bytes_plot(source, is_sender):
    side_name = 'Sender' if is_sender else 'Receiver'

    if is_sender:
        lines = [
            linedesc('MBSent', 'Sent', 'green'),
            linedesc('MBSndDrop', 'Dropped', 'red')
        ]
    else:
        lines = [
            linedesc('MBRecv', 'Received', 'green'),
            linedesc('MBRcvDrop', 'Dropped', 'red'),
        ]

    return create_plot(
        'Megabytes (' + side_name + ' Side)',
        'Time (ms)',
        'MB',
        source,
        lines,
        models.NumeralTickFormatter(format='0,0.00')
    )


def create_rate_plot(source, is_sender):
    side_name = 'Sending' if is_sender else 'Receiving'

    if is_sender:
        lines = [
            linedesc('mbpsSendRate', 'Sendrate', 'green'),
            # Please don't delete the following line.
            # It is used in some cases.
            #linedesc('mbpsMaxBW', 'Bandwidth Limit', 'black'),
        ]
    else:
        lines = [linedesc('mbpsRecvRate', '', 'green')]

    return create_plot(
        side_name + ' Rate',
        'Time (ms)',
        'Rate (Mbps)',
        source,
        lines,
        models.NumeralTickFormatter(format='0,0.00')
    )


def create_rtt_plot(source):
    lines = [linedesc('msRTT', '', 'blue')]

    return create_plot(
        'Round-Trip Time',
        'Time (ms)',
        'RTT (ms)',
        source,
        lines
    )


def create_pkt_send_period_plot(source):
    lines = [linedesc('usPktSndPeriod', '', 'blue')]

    return create_plot(
        'Packet Sending Period',
        'Time (ms)',
        'Period (μs)',
        source,
        lines
    )


def create_avail_buffer_plot(source, is_sender):
    side_name = 'Sending' if is_sender else 'Receiving'

    if is_sender:
        if not 'byteAvailSndBuf' in source.column_names:
            return None
        lines = [linedesc('MBAvailSndBuf', '', 'green')]
    else:
        if not 'byteAvailRcvBuf' in source.column_names:
            return None
        lines = [linedesc('MBAvailRcvBuf', '', 'green')]

    return create_plot(
        'Available ' + side_name + ' Buffer Size',
        'Time (ms)',
        'MB',
        source,
        lines,
        models.NumeralTickFormatter(format='0,0.00')
    )


def create_window_size_plot(source):
    lines = [
        linedesc('pktFlowWindow', 'Flow Window', 'green'),
        linedesc('pktCongestionWindow', 'Congestion Window', 'red'),
    ]

    return create_plot(
        'Window Size',
        'Time (ms)',
        'Number of Packets',
        source,
        lines,
        models.NumeralTickFormatter(format='0,0')
    )
	
def create_buf_timespan_plot(source, is_sender):
    if is_sender and 'msSndBuf' in source.column_names:
        lines = [linedesc('msSndBuf', '', 'blue')]

        return create_plot(
            'Sender Buffer Fullness',
            'Time (ms)',
            'Timespan (ms)',
            source,
            lines
        )

    if  (not is_sender) and 'msRcvBuf' in source.column_names:
        lines = [linedesc('msRcvBuf', '', 'blue')]

        return create_plot(
            'Receiver Buffer Fullness',
            'Time (ms)',
            'Timespan (ms)',
            source,
            lines
        )

    return None

def create_latency_plot(source):
    if 'RCVLATENCYms' in source.column_names:
        lines = [linedesc('RCVLATENCYms', '', 'blue')]

        return create_plot(
            'Latency',
            'Time (ms)',
            'Latency (ms)',
            source,
            lines
        )

    return None


def create_bandwidth_plot(source):
    lines = [linedesc('mbpsBandwidth', '', 'green')]

    return create_plot(
        'Bandwith',
        'Time (ms)',
        'Bandwith (Mbps)',
        source,
        lines,
        models.NumeralTickFormatter(format='0,0')
    )


# TODO: Implement
# def plot_from_dir(dir_path):
#     stats_dir = dir_path
#     for filename in os.listdir(stats_dir):
#         if filename.endswith('.csv'):
#             name, _ = filename.split('.')
#             stats_file = stats_dir + '/' + filename
#             output_file = stats_dir + '/' + name + '.html'
#             plot(stats_file, output_file)


# TODO: Move FEC related calculations out of this script
def calculate_fec_stats(stats_file):
    df = pd.read_csv(stats_file)

    # Calculate summary and average FEC overhead
    df1 = df.sum(axis=0)
    srt_packets = (
        df1['pktRecv'] - df1['pktRcvFilterExtra']
    )  # srt packets only without extra FEC packets
    sum_overhead = round(df1['pktRcvFilterExtra'] * 100 / srt_packets, 2)

    s = df['pktRcvFilterExtra'] * 100 / (df['pktRecv'] - df['pktRcvFilterExtra'])
    avg_overhead = s.sum() / s.size
    avg_overhead = round(avg_overhead, 4)

    # Reconstructed and Not reconstructed packets
    sum_reconstructed = round(df1['pktRcvFilterSupply'] * 100 / srt_packets, 2)
    sum_not_reconstructed = round(df1['pktRcvFilterLoss'] * 100 / srt_packets, 2)

    print(f'fec_overhead: {sum_overhead} %')
    # print(f'avg_overhead: {avg_overhead} %')
    print(f'fec_reconstructed: {sum_reconstructed} %')
    print(f'fec_not_reconstructed: {sum_not_reconstructed} %')


def calculate_fec_stats_from_directory(dir_path):
    stats_dir = dir_path
    for filename in os.listdir(stats_dir):
        if filename.endswith('.csv'):
            name, _ = filename.split('.')
            stats_file = stats_dir + '/' + filename
            print(stats_file)
            calculate_fec_stats(stats_file)
            calculate_received_packets_stats(stats_file)


def calculate_received_packets_stats(stats_file):
    df = pd.read_csv(stats_file)
    df1 = df.sum(axis=0)
    srt_packets = (
        df1['pktRecv'] - df1['pktRcvFilterExtra']
    )  # srt packets only without extra FEC packets

    lost = round(df1['pktRcvLoss'] * 100 / srt_packets, 2)
    retransmitted = round(df1['pktRcvRetrans'] * 100 / srt_packets, 2)
    dropped = round(df1['pktRcvDrop'] * 100 / srt_packets, 2)
    belated = round(df1['pktRcvBelated'] * 100 / srt_packets, 2)

    print(f'lost: {lost} %')
    print(f'retransmitted: {retransmitted} %')
    print(f'dropped: {dropped} %')
    print(f'belated: {belated} %')


@click.command()
@click.argument(
    'stats_filepath',
    type=click.Path(exists=True)
)
@click.option(
    '--is-sender',
    is_flag=True,
    default=False,
    help=   'Should be set if sender statistics is provided. Otherwise, '
            'it is assumed that receiver statistics is provided.',
    show_default=True
)
@click.option(
    '--is-fec',
    is_flag=True,
    default=False,
    help='Should be set if packet filter (FEC) stats is enabled.',
    show_default=True
)
@click.option(
    '--export-png',
    is_flag=True,
    default=False,
    help='Export plots to .png files.',
    show_default=True
)
def plot_graph(stats_filepath, is_sender, is_fec, export_png):
    """
    This script processes .csv file with SRT core statistics produced by
    test application and visualizes the data. Depending on whether 
    statistics is collected on sender or receiver side, the plots may vary.
    """
    filepath = pathlib.Path(stats_filepath)
    filename = filepath.name

    if not filename.endswith('.csv'):
        raise IsNotCSVFile(f'{filepath} does not correspond to a .csv file')

    name, _ = filename.rsplit('.', 1)
    name_parts = name.split('-')
    html_filename = name + '.html'
    html_filepath = filepath.parent / html_filename

    # Additional input filename checks
    if 'snd' in name_parts and not is_sender:
        print(
            'Stats filename corresponds to a sender statistics, however, '
            'is_sender flag is not set. Further stats processing will be '
            'done as in case of sender statistics.'
        )
        is_sender = True

    if 'rcv' in name_parts and is_sender:
        print(
            'Stats filename corresponds to a receiver statistics, however, '
            'is_sender flag is set in True. Further stats processing will be '
            'done as in case of receiver statistics.'
        )
        is_sender = False

    # Prepare data
    df = pd.read_csv(filepath)

    DIVISOR = 1000000
    df['MBRecv'] = df['byteRecv'] / DIVISOR
    df['MBRcvDrop'] = df['byteRcvDrop'] / DIVISOR
    df['MBSent'] = df['byteSent'] / DIVISOR
    df['MBSndDrop'] = df['byteSndDrop'] / DIVISOR
    if 'byteAvailRcvBuf' in df.columns:
        df['MBAvailRcvBuf'] = df['byteAvailRcvBuf'] / DIVISOR
    if 'byteAvailSndBuf' in df.columns:
        df['MBAvailSndBuf'] = df['byteAvailSndBuf'] / DIVISOR

    source = models.ColumnDataSource(df)

    # Output to static .html file
    plotting.output_file(html_filepath, title="SRT Stats Visualization")

    # A dict for storing plots
    plots = {}

    # Create plots
    # RTT
    plots['rtt'] = create_rtt_plot(source)
    export_plot_png(export_png, plots['rtt'], name, 'rtt')

    # Packets Statistics (receiver or sender)
    plots['packets'] = create_packets_plot(source, is_sender)
    export_plot_png(export_png, plots['packets'], name, 'packets')

    # Bandwidth
    plots['bw'] = create_bandwidth_plot(source)

    # Sending / Receiving Rate
    plots['rate'] = create_rate_plot(source, is_sender)
    export_plot_png(export_png, plots['rate'], name, 'rate')

    # Sending / Receiving Bytes
    plots['bytes'] = create_bytes_plot(source, is_sender)

    # Window Size
    plots['window_size'] = create_window_size_plot(source)

    # Latency
    #plots['latency'] = create_latency_plot(source)
    plots['msbuf'] = create_buf_timespan_plot(source, is_sender)

    # Packet Sending Period
    plot_packet_period = None
    if is_sender:
        plot_packet_period = create_pkt_send_period_plot(source)
        # TODO: ? Why plot_packet_period is here?
        # Function create_pkt_send_period_plot does not return None
        if export_png and plot_packet_period:
            # The following two lines remove toolbar from PNG
            plot_packet_period.toolbar.logo = None
            plot_packet_period.toolbar_location = None
            bokeh.io.export_png(
                plot_packet_period, filename=f'{name}-pktsendperiod.png'
            )
        plots['packet_sending_period'] = plot_packet_period

    # Available Buffers
    plot_avail_1 = create_avail_buffer_plot(source, is_sender)
    if export_png and plot_avail_1:
        plot_avail_1.toolbar.logo = None
        plot_avail_1.toolbar_location = None
        bokeh.io.export_png(plot_avail_1, filename=f'{name}-availbuffer.png')
    if plot_avail_1:
        plots['available_buffer_snd'] = plot_avail_1

    plot_avail_2 = create_avail_buffer_plot(source, not is_sender)
    if plot_avail_2:
        plots['available_buffer_rcv'] = plot_avail_2

    # Receiver Statisitcs
    plot_fec = None
    if is_fec:
        plot_fec = plotting.figure(
            plot_width=PLOT_WIDTH,
            plot_height=PLOT_HEIGHT,
            tools=TOOLS
        )
        plot_fec.title.text = 'FEC - Packets (Receiver Side)'
        plot_fec.xaxis.axis_label = 'Time (ms)'
        plot_fec.yaxis.axis_label = 'Number of Packets'
        plot_fec.line(
            x='Time',
            y='pktRcvFilterExtra',
            color='blue',
            legend_label='Extra received',
            source=source,
        )
        plot_fec.line(
            x='Time',
            y='pktRcvFilterSupply',
            color='green',
            legend_label='Reconstructed',
            source=source,
        )
        plot_fec.line(
            x='Time',
            y='pktRcvFilterLoss',
            color='red',
            legend_label='Not reconstructed',
            source=source,
        )

        plots['fec'] = plot_fec

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
            [plots['packets'], plots['window_size']],
            [plots['bytes'], plots['rtt']],
            [plots['rate'], plots['bw']],
            [plot_packet_period, plots['msbuf']],
            [plot_avail_1, plot_avail_2],
            [plot_fec],
        ]
    )
    plotting.show(grid)


if __name__ == '__main__':
    plot_graph()
