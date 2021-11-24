"""
'''
Description: the utilities of evaluation
Version: 2.0.0.20211124
Author: Arvin Zhao
Date: 2021-11-21 14:50:13
Last Editors: Arvin Zhao
LastEditTime: 2021-11-24 14:39:27
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

    def __make_throughput_plot(
        self,
        base_dir: str,
        colours,
        experiments: list,
        group: str,
        has_sfq_only: bool,
        n: int,
    ) -> None:
        """Make a plot indicating the flow throughput over time.

        Parameters
        ----------
        base_dir : str
            The name of the output base directory.
        colours :
            A customised colour map.
        experiments : list
            A list of experiment names.
        group : str
            The experiment group.
        has_sfq_only : bool
            A flag indicating if the AQM algorithm on the plot only has SFQ.
        n : int
            The number of the hosts on each side of the dumbbell topology.
        """
        info(
            "*** Plotting " + "the baseline and SFQ's"
            if has_sfq_only
            else "each AQM algorithm's"
            + f" flow throughput over time for the group: {group}\n"
        )
        plt.figure()
        plt.title("Throughput over time" if has_sfq_only else "Fairness")

        for experiment, colour in zip(experiments, colours):
            if (has_sfq_only and experiment in ["baseline", "sfq"]) or (
                not has_sfq_only and experiment != "baseline"
            ):
                for i in range(n):
                    data = pd.read_csv(
                        os.path.join(
                            base_dir, experiment, f"hl{i + 1}", self.__file_formatted
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
        plt.savefig(
            os.path.join(
                base_dir, "throughput_sfq.png" if has_sfq_only else "throughput.png"
            )
        )

    def plot_throughput(
        self, group: str, bw: int = 1, bw_unit: str = "gbit", n: int = 2
    ) -> None:
        """Plot the flow throughput over time for the specified experiment group.

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
        group = group.strip()
        base_dir = os.path.join(self.__base_dir, f"{n}f", group, f"{bw}{bw_unit}")
        experiments = sorted(
            [entry.name for entry in os.scandir(base_dir) if entry.is_dir()]
        )
        colours = plt.cm.jet(np.linspace(0, 1, len(experiments)))

        for has_sfq_only in [True, False]:
            self.__make_throughput_plot(
                base_dir=base_dir,
                colours=colours,
                experiments=experiments,
                group=group,
                has_sfq_only=has_sfq_only,
                n=n,
            )

    def plot_utilisation(
        self, group: str, bw: int = 1, bw_unit: str = "gbit", n: int = 2
    ) -> None:
        """Plot each AQM algorithm's link utilisation by comparing the aggregate throughput with the available bandwidth for the specified experiment group.

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
            f"*** Plotting each AQM algorithm's link utilisation for the group: {group}\n"
        )
        plt.figure()
        plt.title("Link utilisation")
        base_dir = os.path.join(self.__base_dir, f"{n}f", group, f"{bw}{bw_unit}")
        experiments = sorted(
            [
                entry.name
                for entry in os.scandir(base_dir)
                if entry.is_dir() and entry.name != "baseline"
            ]
        )
        results = []

        for experiment in experiments:
            throughput = 0

            for i in range(n):
                throughput += pd.read_csv(
                    os.path.join(
                        base_dir, experiment, f"hl{i + 1}", self.__file_formatted
                    ),
                    header=None,
                    sep=" ",
                )[-1:][[1]][1]

            results.append(throughput / (bw * 1000 if bw_unit == "gbit" else bw) * 100)

        for experiment, result in zip(experiments, results):
            plt.bar(experiment, result)

        plt.xlabel("AQM algorithm")
        plt.ylabel("link utilisation (%)")
        plt.ylim(np.min(results) - 5, 100)
        plt.savefig(os.path.join(base_dir, "utilisation.png"))


# Simple test purposes only.
if __name__ == "__main__":
    from experiment import GROUP_B, OUTPUT_BASE_DIR, OUTPUT_FILE_FORMATTED

    eval = Eval(base_dir=OUTPUT_BASE_DIR, file_formatted=OUTPUT_FILE_FORMATTED)
    eval.plot_throughput(group=GROUP_B)
    eval.plot_utilisation(group=GROUP_B)
