"""
'''
Description: the utilities of evaluation
Version: 2.0.0.20211122
Author: Arvin Zhao
Date: 2021-11-21 14:50:13
Last Editors: Arvin Zhao
LastEditTime: 2021-11-22 22:38:43
'''
"""

import os

from mininet.log import info
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from net import check_bw_unit


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
        """Plot each experiment's flow throughput over time for the specified experiment group.

        Parameters
        ----------
        group : str
            The experiment group.
        n : int, optional
            The number of the hosts on each side of the dumbbell topology (the default is 2).
        """
        group = group.strip()
        info(
            f"*** Plotting each experiment's flow throughput over time for the group: {group}\n"
        )
        plt.figure()
        plt.title("Throughput over time")
        experiments = sorted(
            [
                entry.name
                for entry in os.scandir(os.path.join(self.__base_dir, group))
                if entry.is_dir()
            ]
        )
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

    def plot_utilisation(
        self, group: str, bw: int = 1, bw_unit: str = "gbit", n: int = 2
    ) -> None:
        """Plot each experiment's link utilisation by comparing the aggregate throughput with the available bandwidth for the specified experiment group.

        Parameters
        ----------
        group : str
            The experiment group.
        bw : int, optional
            The bandwidth (the default is 1).
        bw_unit : str, optional
            The bandwidth unit (the default is "gbit", and "mbit" is another accepted value).
        n : int, optional
            The number of the hosts on each side of the dumbbell topology (the default is 2).
        """
        bw_unit = check_bw_unit(bw_unit=bw_unit)
        group = group.strip()
        info(
            f"*** Plotting each experiment's link utilisation for the group: {group}\n"
        )
        plt.figure()
        plt.title("Link utilisation")
        experiments = sorted(
            [
                entry.name
                for entry in os.scandir(os.path.join(self.__base_dir, group))
                if entry.is_dir()
            ]
        )
        results = []

        for experiment in experiments:
            throughput = 0

            for i in range(n):
                throughput += pd.read_csv(
                    os.path.join(
                        self.__base_dir,
                        group,
                        experiment,
                        f"hl{i + 1}",
                        self.__file_formatted,
                    ),
                    header=None,
                    sep=" ",
                )[-1:][[1]][1]

            results.append(throughput / (bw * 1000 if bw_unit == "gbit" else bw) * 100)

        for experiment, result in zip(experiments, results):
            plt.bar(experiment, result)

        plt.xlabel("experiment")
        plt.ylabel("link utilisation (%)")
        plt.ylim(np.min(results) - 5, 100)
        plt.savefig(os.path.join(self.__base_dir, group, "utilisation.png"))


# Simple test purposes only.
if __name__ == "__main__":
    from experiment import GROUP_B, OUTPUT_BASE_DIR, OUTPUT_FILE_FORMATTED

    eval = Eval(base_dir=OUTPUT_BASE_DIR, file_formatted=OUTPUT_FILE_FORMATTED)
    eval.plot_throughput(group=GROUP_B)
    eval.plot_utilisation(group=GROUP_B)
