"""
'''
Description: the utilities of evaluation
Version: 2.0.0.20211119
Author: Arvin Zhao
Date: 2021-10-19 15:22:06
Last Editors: Arvin Zhao
LastEditTime: 2021-11-19 19:38:43
'''
"""

import os

from mininet.log import info
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from experiment import OUTPUT_BASE_DIR, SUMMARY_FILE


def import_summary(category: str, group: str) -> pd.DataFrame:
    """Import the corresponding output in the summary file.

    Parameters
    ----------
    category : str
        The category of the output (e.g., FCT).
    group : str
        The experiment group.

    Returns
    -------
    pandas.DataFrame
        The corresponding output for the specified category.

    Raises
    ------
    ValueError
        The category does not exist. Check if the value is one of "FCT" and "throughput".
    """
    category = category.lower().strip()

    if category not in ["fct", "throughput"]:
        raise ValueError("invalid category")
    else:
        columns = (
            [0, 1, 3] if category == "fct" else [0, 2, 4]
        )  # TODO: n = 2 not always

    data = pd.read_csv(
        os.path.join(OUTPUT_BASE_DIR, group, SUMMARY_FILE),
        header=None,
        sep=" ",
    )[columns]
    data.columns = range(len(columns))
    return data


def make_plot(data: pd.DataFrame, path: str, title: str, y_label: str) -> None:
    """Make a line chart.

    Parameters
    ----------
    data : pandas.DataFrame
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
    if not isinstance(data, pd.DataFrame) and data.shape[1] != 3:
        raise ValueError("invalid data to make a line chart")

    ind = np.arange(len(data[0]))
    width = 0.35
    plt.figure()
    plt.bar(ind, data[1], width, label="Source host 1")
    plt.bar(ind + width, data[2], width, label="Source host 2")
    plt.title(label=title)
    plt.legend()
    plt.xlabel("experiment")
    plt.xticks(ind + width / 2, data[0])
    plt.ylabel(y_label)
    plt.savefig(path)


def plot_fct(group: str) -> None:
    """Plot a line chart showing the flow completion time (FCT) over experiments.

    Parameters
    ----------
    group : str
        The experiment group.
    """
    info("*** Plotting FCT over experiments\n")
    make_plot(
        data=import_summary(category="FCT", group=group),
        path=os.path.join(OUTPUT_BASE_DIR, group, "FCT.png"),
        title="FCT over experiments",
        y_label="FCT (sec)",
    )


def plot_throughput(group: str) -> None:
    """Plot a line chart showing the throughput over experiments.

    Parameters
    ----------
    group : str
        The experiment group.
    """
    info("*** Plotting throughput over experiments\n")
    make_plot(
        data=import_summary(category="throughput", group=group),
        path=os.path.join(OUTPUT_BASE_DIR, group, "throughput.png"),
        title="Throughput over experiments",
        y_label="throughput (Mbps)",
    )


# Simple test purposes only.
if __name__ == "__main__":
    plot_fct(group="fairness")
    # TODO: plot_throughput(group="fairness")
