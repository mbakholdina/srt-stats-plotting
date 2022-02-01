# srt-stats-plotting

<p align="left">
<a href="https://github.com/python/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

Script designed to plot graphs out of SRT core statistics.

[SRT](https://github.com/Haivision/srt) stands for Secure Reliable Transport and is an open source transport technology that optimizes streaming performance across unpredictable networks, such as the Internet.

## Requirements

* python 3.6+
* PhantomJS 2.1 optional to [export plots](https://bokeh.pydata.org/en/latest/docs/user_guide/export.html)

To install the library dependencies run:
```
pip install -r requirements.txt
```

## Script Usage

The main purpose of `plot_srt_stats.py` script is to visualize all the SRT core statistics produced during experiments by one of the [testing applications](https://github.com/Haivision/srt/blob/master/docs/apps/srt-live-transmit.md) or third-party solutions supporting SRT protocol. Depending on whether this statistics is collected on sender or receiver side, the data plotted may vary.

SRT core statistics should be collected in a `.csv` file. Usually, as a naming convention rule the file name ends either on "-snd" or "-rcv" depending on the side (sender or receiver) where the data was collected. Or, file name can just contain "snd" or "rcv" part in it.

Statistics filepath is passed as an argument to a script. Script usage
```
plot_srt_stats.py [OPTIONS] STATS_FILEPATH
```

Use `--help` option in order to get the full list of options
```
--is-sender   Should be set if sender statistics is provided. Otherwise, it
              is assumed that receiver statistics is provided.
--is-fec      Should be set if packet filter (FEC) stats is enabled.
--export-png  Export plots to .png files.
--help        Show this message and exit.
```

## Usage with srt-live-transmit
For the usage with [srt-live-transmit](https://github.com/Haivision/srt/blob/master/docs/apps/srt-live-transmit.md), make sure that the export of SRT statistics is enabled in .csv format. This can be done by passing the following parameters:
- ` -statspf:csv` to ensure the CSV format is used when exporting.
- ` -statsout:/path/to/desired/folder/filename-rcv.csv` to define where to write the statistics
- ` -stats-report-frequency:1000` to define how often to write statistics (per # of packets), this example sets it to once per thousand packets.

More information on srt-live-transmit's command line parameters can be found [here](https://github.com/Haivision/srt/blob/master/docs/apps/srt-live-transmit.md#command-line-options).

## Plots Description

**Note:** Megabytes and Rate plots correlation is determined by the following formula

_Rate (Mbps) = MB / interval (s),_

where _interval_ is the interval indicating how frequently the statistics is collected (in seconds).


## Example Plots

The script plots different charts from SRT statistics. Examples of `.csv` files and corresponding `.html` output can be found in the [examples](https://github.com/mbakholdina/srt-stats-plotting/tree/master/examples) folder. For example, a chart to visualize statistics on the packets being sent, lost, retransmitted, dropped or on flight:

<img src="img/packets_1.png" alt="packets_1" style="zoom:50%;" />

The legends are interactive. You can click, e.g., on `Dropped` and `On Flight` to disable the respective plots:

<img src="img/packets_2.png" alt="packets_2" style="zoom:50%;" />

Another chart illustrates the sending rate in Mbps:

<img src="img/sending_rate_mbps.png" alt="sending_rate_mbps" style="zoom:50%;" />

Available size of the sender's buffer helps to detect if there is enough space to store outgoing data, or the source generates data faster then SRT can transmit:

<img src="img/available_snd_buffer_size.png" alt="available_snd_buffer_size" style="zoom:50%;" />
