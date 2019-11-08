from collections import namedtuple
import os
import pathlib

import bokeh.io
import bokeh.layouts as layouts
import bokeh.models as models
import bokeh.plotting as plotting
import click
import pandas as pd


PLOT_WIDTH = 800
PLOT_HEIGHT = 300
linedesc = namedtuple("linedesc", ['col', 'legend', 'color'])


class IsNotCSVFile(Exception):
    pass


def create_plot(title, xlabel, ylabel, source, lines, yformatter=None):
    fig = plotting.figure(plot_width=PLOT_WIDTH, plot_height=PLOT_HEIGHT)
    fig.title.text = title
    fig.xaxis.axis_label = xlabel
    fig.yaxis.axis_label = ylabel

    fig.xaxis.formatter = models.NumeralTickFormatter(format='0,0')
    if yformatter is not None:
        fig.yaxis.formatter = yformatter

    for x in lines:
        fig.line(x='Time', y=x.col, color=x.color, legend=x.legend, source=source)

    return fig


def create_packets_plot(source, is_sender):
    side_name = 'Sender' if is_sender else 'Receiver'

    # Use a list of named tuples to select data columns
    if is_sender:
        cols = [
            linedesc('pktSent', 'Sent', 'green'),
            linedesc('pktSndLoss', 'Lost', 'orange'),
            linedesc('pktRetrans', 'Retransmitted', 'blue'),
            linedesc('pktSndDrop', 'Dropped', 'red'),
            linedesc('pktFlightSize', 'On Flight', 'black'),
        ]
    else:
        cols = [
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
        cols,
        models.NumeralTickFormatter(format='0,0')
    )


def create_bytes_plot(source, is_sender, df):
    side_name = 'Sender' if is_sender else 'Receiver'

    # Use a list of named tuples to select data columns
    if is_sender:
        cols = [
            linedesc('MBSent', 'Sent', 'green'),
            linedesc('MBSndDrop', 'Dropped', 'red')
        ]

        # if 'byteAvailSndBuf' in df.columns:
        #    cols.append(linedesc('byteAvailSndBuf', 'Available SND Buffer', 'black'))
    else:
        cols = [
            linedesc('MBRecv', 'Received', 'green'),
            linedesc('MBRcvDrop', 'Dropped', 'red'),
        ]

    return create_plot(
        'Megabytes (' + side_name + ' Side)',
        'Time (ms)',
        'MB',
        source,
        cols,
        models.NumeralTickFormatter(format='0,0.00')
    )


def create_rate_plot(source, is_sender):
    side_name = 'Sending' if is_sender else 'Receiving'

    # Use a list of named tuples to select data columns
    if is_sender:
        cols = [
            linedesc('mbpsSendRate', None, 'green'),
            #linedesc('mbpsMaxBW', 'Bandwidth Limit', 'black')
        ]
    else:
        cols = [linedesc('mbpsRecvRate', '', 'green')]

    return create_plot(
        side_name + ' Rate',
        'Time (ms)',
        'Rate (Mbps)',
        source,
        cols,
        models.NumeralTickFormatter(format='0,0.00')
    )


def create_rtt_plot(source):
    cols = [linedesc('msRTT', '', 'blue')]

    return create_plot(
        'Round-Trip Time',
        'Time (ms)',
        'RTT (ms)',
        source,
        cols
    )


def create_pkt_send_period_plot(source):
    cols = [linedesc('usPktSndPeriod', '', 'blue')]

    return create_plot(
        'Packet Sending Period',
        'Time (ms)',
        'Period (μs)',
        source,
        cols
    )


def create_avail_buffer_plot(source, is_sender, df):
    side_name = 'Sending' if is_sender else 'Receiving'

    # Use a list of named tuples to select data columns
    if is_sender:
        if not 'byteAvailSndBuf' in df.columns:
            return None
        cols = [linedesc('MBAvailSndBuf', '', 'green')]
    else:
        if not 'byteAvailRcvBuf' in df.columns:
            return None
        cols = [linedesc('MBAvailRcvBuf', '', 'green')]

    return create_plot(
        'Available ' + side_name + ' Buffer Size',
        'Time (ms)',
        'MB',
        source,
        cols,
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
    """ TODO """
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

    # Create plots
    plot_rtt = create_rtt_plot(source)
    if export_png:
        # The following two lines remove toolbar from PNG
        plot_rtt.toolbar.logo = None
        plot_rtt.toolbar_location = None
        bokeh.io.export_png(plot_rtt, filename=f'{name}-rtt.png')

    # Packets Statistics plot (receiver or sender)
    plot_packets = create_packets_plot(source, is_sender)
    if export_png:
        # The following two lines remove toolbar from PNG
        plot_packets.toolbar.logo = None
        plot_packets.toolbar_location = None
        bokeh.io.export_png(plot_packets, filename=f'{name}-packets.png')

    plot_bw = plotting.figure(plot_width=PLOT_WIDTH, plot_height=PLOT_HEIGHT)
    plot_bw.title.text = 'Bandwith'
    plot_bw.xaxis.axis_label = 'Time (ms)'
    plot_bw.yaxis.axis_label = 'Bandwith (Mbps)'
    plot_bw.xaxis.formatter = models.NumeralTickFormatter(format='0,0')
    plot_bw.yaxis.formatter = models.NumeralTickFormatter(format='0,0')
    plot_bw.line(x='Time', y='mbpsBandwidth', color='green', source=source)

    # Sending / Receiving Rate plot
    plot_rate = create_rate_plot(source, is_sender)
    if export_png:
        # The following two lines remove toolbar from PNG
        plot_rate.toolbar.logo = None
        plot_rate.toolbar_location = None
        bokeh.io.export_png(plot_rate, filename=f'{name}-rate.png')

    # Sending / Receiving Bytes plot
    plot_bytes = create_bytes_plot(source, is_sender, df)

    plot_window_size = plotting.figure(plot_width=PLOT_WIDTH, plot_height=PLOT_HEIGHT)
    plot_window_size.title.text = 'Window Size'
    plot_window_size.xaxis.axis_label = 'Time (ms)'
    plot_window_size.yaxis.axis_label = 'Number of Packets'
    plot_window_size.xaxis.formatter = models.NumeralTickFormatter(format='0,0')
    plot_window_size.yaxis.formatter = models.NumeralTickFormatter(format='0,0')
    plot_window_size.line(
        x='Time', y='pktFlowWindow', color='green', legend='Flow Window', source=source
    )
    plot_window_size.line(
        x='Time',
        y='pktCongestionWindow',
        color='red',
        legend='Congestion Window',
        source=source,
    )

    plot_latency = None
    if 'RCVLATENCYms' in df.columns:
        plot_latency = plotting.figure(plot_width=PLOT_WIDTH, plot_height=PLOT_HEIGHT)
        plot_latency.title.text = 'Latency'
        plot_latency.xaxis.axis_label = 'Time (ms)'
        plot_latency.yaxis.axis_label = 'Latency (ms)'
        plot_latency.line(x='Time', y='RCVLATENCYms', color='blue', source=source)

    plot_packet_period = None
    if is_sender:
        plot_packet_period = create_pkt_send_period_plot(source)
        if export_png and plot_packet_period:
            # The following two lines remove toolbar from PNG
            plot_packet_period.toolbar.logo = None
            plot_packet_period.toolbar_location = None
            bokeh.io.export_png(
                plot_packet_period, filename=f'{name}-pktsendperiod.png'
            )

    plot_avail_1 = create_avail_buffer_plot(source, is_sender, df)
    if export_png and plot_avail_1:
        # The following two lines remove toolbar from PNG
        plot_avail_1.toolbar.logo = None
        plot_avail_1.toolbar_location = None
        bokeh.io.export_png(plot_avail_1, filename=f'{name}-availbuffer.png')

    plot_avail_2 = create_avail_buffer_plot(source, not is_sender, df)

    # Receiver Statisitcs
    plot_fec = None
    if is_fec:
        plot_fec = plotting.figure(plot_width=PLOT_WIDTH, plot_height=PLOT_HEIGHT)
        plot_fec.title.text = 'FEC - Packets (Receiver Side)'
        plot_fec.xaxis.axis_label = 'Time (ms)'
        plot_fec.yaxis.axis_label = 'Number of Packets'
        plot_fec.line(
            x='Time',
            y='pktRcvFilterExtra',
            color='blue',
            legend='Extra received',
            source=source,
        )
        plot_fec.line(
            x='Time',
            y='pktRcvFilterSupply',
            color='green',
            legend='Reconstructed',
            source=source,
        )
        plot_fec.line(
            x='Time',
            y='pktRcvFilterLoss',
            color='red',
            legend='Not reconstructed',
            source=source,
        )

    # Show the results
    grid = layouts.gridplot(
        [
            [plot_packets, plot_window_size],
            [plot_bytes, plot_rtt],
            [plot_rate, plot_bw],
            [plot_packet_period, plot_latency],
            [plot_avail_1, plot_avail_2],
            [plot_fec],
        ]
    )
    plotting.show(grid)


if __name__ == '__main__':
    plot_graph()