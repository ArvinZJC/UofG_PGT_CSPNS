"""
'''
Description: the utilities of evaluation
Version: 1.0.0.20211026
Author: Arvin Zhao
Date: 2021-10-19 15:22:06
Last Editors: Arvin Zhao
LastEditTime: 2021-10-26 21:42:42
'''
"""

import os

import matplotlib.pyplot as plt
import pandas as pd

from experiment import OUTPUT_BASE_DIR, OUTPUT_FILE_FORMATTED

HOST_NUMS = [1, 2]  # A list of host numbers.


def import_output(type: str) -> pd.DataFrame:
    """Import the output from the output file.

    Parameters
    ----------
    type : str
        The type of the output (e.g., RTT).

    Returns
    -------
    list
        The corresponding output of each host.

    Raises
    ------
    ValueError
        The type does not exist. Check if the value is one of "RTT" and "throughput".
    """
    type = type.lower().strip()

    if type not in ["rtt", "throughput"]:
        raise ValueError("invalid type")
    else:
        col_idx = 1 if type == "throughput" else 2

    return [
        pd.read_csv(
            os.path.join(OUTPUT_BASE_DIR, f"h{i}", OUTPUT_FILE_FORMATTED),
            header=None,
            sep=" ",
        )[:-1][col_idx]
        for i in HOST_NUMS
    ]


def make_plot(data: list, path: str, title: str, y_label: str) -> None:
    """Make a line chart.

    Parameters
    ----------
    data : list
        The data to make a line chart.
    path : str
        The path to save the chart.
    title : str
        The chart title.
    y_label : str
        The y-axis label of the chart.

    Raises
    ------
    ValueError
        The data to make a line chart is invalid. Check if the data is a list and each element is a pandas dataframe.
    """
    if not isinstance(data, list) or len(data) != 2:
        raise ValueError("invalid data to make a line chart")
    else:
        for i in data:
            if not isinstance(i, pd.Series):
                raise ValueError("invalid data elements to make a line chart")

    plt.figure()
    plt.plot(range(1, data[0].size + 1), data[0], label="Host 1")
    plt.plot(range(1, data[1].size + 1), data[1], label="Host 2")
    plt.title(label=title)
    plt.legend()
    plt.xlabel("time (sec)")
    plt.ylabel(y_label)
    plt.savefig(path)


def plot_rtt() -> None:
    """Plot a line chart showing the RTT over time."""
    make_plot(
        data=import_output(type="RTT"),
        path=os.path.join(OUTPUT_BASE_DIR, "RTT.png"),
        title="RTT over time",
        y_label="RTT (us)",
    )


def plot_throughput() -> None:
    """Plot a line chart showing the throughput over time."""
    make_plot(
        data=import_output(type="throughput"),
        path=os.path.join(OUTPUT_BASE_DIR, "throughput.png"),
        title="Throughput over time",
        y_label="throughput (Mbps)",
    )


# Simple test purposes only.
if __name__ == "__main__":
    plot_rtt()
    plot_throughput()