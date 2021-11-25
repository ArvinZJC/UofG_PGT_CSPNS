"""
'''
Description: the utilities of evaluation
Version: 2.0.0.20211125
Author: Arvin Zhao
Date: 2021-11-21 14:50:13
Last Editors: Arvin Zhao
LastEditTime: 2021-11-25 15:19:58
'''
"""

import os

from mininet.log import info
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from experiment import GROUP_B
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
        self.__PIE = "pie"  # The name of the experiment for PIE.
        self.__RED = "red"  # The name of the experiment for RED.
        self.__SFQ = "sfq"  # The name of the experiment for SFQ.
        self.__TBF = "baseline"  # The name of the experiment for the baseline.
        self.__base_dir = base_dir
        self.__file_formatted = file_formatted

    def __make_cwnd_plot(
        self,
        base_dir: str,
        bw: int,
        bw_unit: str,
        colours: np.ndarray,
        experiments: list,
        n: int,
        name: str,
    ) -> None:
        """Make a plot indicating the flow CWND over time.

        Parameters
        ----------
        base_dir : str
            The name of the output base directory.
        bw : int
            The bandwidth (the default is 1).
        bw_unit : str
            The bandwidth unit (the default is "gbit", and "mbit" is another accepted value).
        colours : numpy.ndarray
            A customised colour map.
        experiments : list
            A list of experiment names.
        n : int
            The number of the hosts on each side of the dumbbell topology.
        name : str
            The name of an experiment for an AQM algorithm to compare with the baseline.
        """
        info(
            f"*** Plotting the baseline and the AQM algorithm's flow CWND over time: {n}f - {GROUP_B} - {bw}{bw_unit} - {name}\n"
        )
        plt.figure()
        plt.title("CWND over time")

        for experiment, colour in zip(experiments, colours):
            if experiment == self.__TBF or experiment == name:
                for i in range(n):
                    data = pd.read_csv(
                        os.path.join(
                            base_dir, experiment, f"hl{i + 1}", self.__file_formatted
                        ),
                        header=None,
                        sep=" ",
                    )[:-1][[0, 2]]
                    plt.plot(
                        data[0],
                        data[2],
                        color=colour,
                        label=experiment if i == 0 else None,
                    )

        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.xlabel("time (sec)")
        plt.ylabel("CWND (MB)")
        plt.tight_layout()
        plt.savefig(os.path.join(base_dir, f"cwnd_{name}.png"))

    def __make_throughput_plot(
        self,
        base_dir: str,
        bw: int,
        bw_unit: str,
        colours: np.ndarray,
        experiments: list,
        has_sfq_only: bool,
        n: int,
    ) -> None:
        """Make a plot indicating the flow throughput over time.

        Parameters
        ----------
        base_dir : str
            The name of the output base directory.
        bw : int
            The bandwidth (the default is 1).
        bw_unit : str
            The bandwidth unit (the default is "gbit", and "mbit" is another accepted value).
        colours : numpy.ndarray
            A customised colour map.
        experiments : list
            A list of experiment names.
        has_sfq_only : bool
            A flag indicating if the AQM algorithm on the plot only has SFQ.
        n : int
            The number of the hosts on each side of the dumbbell topology.
        """
        info(
            "*** Plotting "
            + ("the baseline and SFQ's" if has_sfq_only else "each AQM algorithm's")
            + f" flow throughput over time: {n}f - {GROUP_B} - {bw}{bw_unit}\n"
        )
        plt.figure()
        plt.title("Throughput over time" if has_sfq_only else "Fairness")

        for experiment, colour in zip(experiments, colours):
            if (has_sfq_only and experiment in [self.__TBF, self.__SFQ]) or (
                not has_sfq_only and experiment != self.__TBF
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

    def plot_cwnd(self, bw: int = 1, bw_unit: str = "gbit", n: int = 1) -> None:
        """Plot the flow CWND over time for the group transferring data for the specified/same time length.

        Parameters
        ----------
        bw : int, optional
            The bandwidth (the default is 1).
        bw_unit : str, optional
            The bandwidth unit (the default is "gbit", and "mbit" is another accepted value).
        n : int, optional
            The number of the hosts on each side of the dumbbell topology (the default is 1).
        """
        base_dir = os.path.join(self.__base_dir, f"{n}f", GROUP_B, f"{bw}{bw_unit}")
        experiments = sorted(
            [entry.name for entry in os.scandir(base_dir) if entry.is_dir()]
        )
        colours = plt.cm.jet(np.linspace(0, 1, len(experiments)))

        for name in [self.__PIE, self.__RED]:
            self.__make_cwnd_plot(
                base_dir=base_dir,
                bw=bw,
                bw_unit=bw_unit,
                colours=colours,
                experiments=experiments,
                n=n,
                name=name,
            )

    def plot_throughput(self, bw: int = 1, bw_unit: str = "gbit", n: int = 2) -> None:
        """Plot the flow throughput over time for the group transferring data for the specified/same time length.

        Parameters
        ----------
        bw : int, optional
            The bandwidth (the default is 1).
        bw_unit : str, optional
            The bandwidth unit (the default is "gbit", and "mbit" is another accepted value).
        n : int, optional
            The number of the hosts on each side of the dumbbell topology (the default is 2).
        """
        base_dir = os.path.join(self.__base_dir, f"{n}f", GROUP_B, f"{bw}{bw_unit}")
        experiments = sorted(
            [entry.name for entry in os.scandir(base_dir) if entry.is_dir()]
        )
        colours = plt.cm.jet(np.linspace(0, 1, len(experiments)))

        for has_sfq_only in [True, False]:
            self.__make_throughput_plot(
                base_dir=base_dir,
                bw=bw,
                bw_unit=bw_unit,
                colours=colours,
                experiments=experiments,
                has_sfq_only=has_sfq_only,
                n=n,
            )

    def plot_utilisation(self, bw: int = 1, bw_unit: str = "gbit", n: int = 1) -> None:
        """Plot each AQM algorithm's link utilisation for the group transferring data for the specified/same time length.

        Parameters
        ----------
        bw : int, optional
            The bandwidth (the default is 1).
        bw_unit : str, optional
            The bandwidth unit (the default is "gbit", and "mbit" is another accepted value).
        n : int, optional
            The number of the hosts on each side of the dumbbell topology (the default is 1).
        """
        bw_unit = check_bw_unit(bw_unit=bw_unit)
        base_dir = os.path.join(self.__base_dir, f"{n}f", GROUP_B, f"{bw}{bw_unit}")
        info(
            f"*** Plotting each AQM algorithm's link utilisation: {n}f - {GROUP_B} - {bw}{bw_unit}\n"
        )
        plt.figure()
        plt.title("Link utilisation")
        experiments = sorted(
            [
                entry.name
                for entry in os.scandir(base_dir)
                if entry.is_dir() and entry.name != self.__TBF
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
    from mininet.log import setLogLevel
    from experiment import OUTPUT_BASE_DIR, OUTPUT_FILE_FORMATTED

    setLogLevel("info")
    eval = Eval(base_dir=OUTPUT_BASE_DIR, file_formatted=OUTPUT_FILE_FORMATTED)
    eval.plot_cwnd()
    eval.plot_throughput()
    eval.plot_utilisation()
