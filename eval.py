"""
'''
Description: the utilities of evaluation
Version: 2.0.0.20211121
Author: Arvin Zhao
Date: 2021-11-21 14:50:13
Last Editors: Arvin Zhao
LastEditTime: 2021-11-21 21:40:55
'''
"""

import os

from mininet.log import info
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class Eval:
    """The class for defining the utilities of evaluation."""

    def __init__(self, base_dir: str, file_formatted: str) -> None:
        """The constructor of the class for defining the utilities of evaluation.

        Parameters
        ----------
        base_dir : str
            The name of the output base directory.
        file_formatted : str
            The filename with the file extension of the formatted output file.
        """
        self.__base_dir = base_dir
        self.__file_formatted = file_formatted

    def plot_throughput(self, group: str, n: int = 2) -> None:
        """Plot each experiment's throughput over time for the specified experiment group.

        Parameters
        ----------
        group : str
            The experiment group.
        n : int, optional
            The number of the hosts on each side of the dumbbell topology (the default is 2).
        """
        info(
            f"*** Plotting each experiment's throughput over time for the group: {group}\n"
        )
        plt.figure()
        plt.title("Throughput over time")
        experiments = [
            entry.name
            for entry in os.scandir(os.path.join(self.__base_dir, group))
            if entry.is_dir()
        ]
        colours = plt.cm.jet(np.linspace(0, 1, len(experiments)))

        for experiment, colour in zip(experiments, colours):
            for i in range(n):
                data = pd.read_csv(
                    os.path.join(
                        self.__base_dir,
                        group,
                        experiment,
                        f"hl{i + 1}",
                        self.__file_formatted,
                    ),
                    header=None,
                    sep=" ",
                )[:-1][[0, 1]]
                plt.plot(
                    data[0],
                    data[1],
                    color=colour,
                    label=experiment if i == 0 else None,
                )

        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.xlabel("time (sec)")
        plt.ylabel("throughput (Mbps)")
        plt.tight_layout()
        plt.savefig(os.path.join(self.__base_dir, group, "throughput.png"))


# Simple test purposes only.
if __name__ == "__main__":
    from experiment import GROUP_B, OUTPUT_BASE_DIR, OUTPUT_FILE_FORMATTED

    eval = Eval(base_dir=OUTPUT_BASE_DIR, file_formatted=OUTPUT_FILE_FORMATTED)
    eval.plot_throughput(group=GROUP_B)
