"""
'''
Description: the utilities of evaluation
Version: 2.0.0.20211125
Author: Arvin Zhao
Date: 2021-11-21 14:50:13
Last Editors: Arvin Zhao
LastEditTime: 2021-11-25 23:33:07
'''
"""

import os

from mininet.log import info
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from experiment import GROUP_A, GROUP_B


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
        self.__BW_NAME_DEFAULT = (
            "1gbit"  # The default name of the experiment's bandwidth.
        )
        self.__FLOW_1 = "1f"  # The name of the experiment using 1 flow.
        self.__FLOW_2 = "2f"  # The name of the experiment using 2 flows.
        self.__CODEL = "codel"  # The name of the experiment for CoDel.
        self.__PIE = "pie"  # The name of the experiment for PIE.
        self.__RED = "red"  # The name of the experiment for RED.
        self.__SFQ = "sfq"  # The name of the experiment for SFQ.
        self.__TBF = "baseline"  # The name of the experiment for the baseline.
        self.__base_dir = base_dir
        self.__file_formatted = file_formatted

    def __make_cwnd_plot(
        self, base_dir: str, colours: np.ndarray, experiments: list, name: str
    ) -> None:
        """Make a plot indicating the flow CWND over time.

        Parameters
        ----------
        base_dir : str
            The name of the output base directory.
        colours : numpy.ndarray
            A customised colour map.
        experiments : list
            A list of experiment names.
        name : str
            The name of an experiment for an AQM algorithm to compare with the baseline.
        """
        info(
            f"*** Plotting the baseline and the AQM algorithm's flow CWND over time: {self.__FLOW_1} - {GROUP_B} - {self.__BW_NAME_DEFAULT} - {name}\n"
        )
        plt.figure()
        plt.title("CWND over time")

        for experiment, colour in zip(experiments, colours):
            if experiment == self.__TBF or experiment == name:
                data = pd.read_csv(
                    os.path.join(base_dir, experiment, "hl1", self.__file_formatted),
                    header=None,
                    sep=" ",
                )[:-1][[0, 2]]
                plt.plot(data[0], data[2], color=colour, label=experiment)

        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.xlabel("time (sec)")
        plt.ylabel("CWND (MB)")
        plt.tight_layout()
        plt.savefig(os.path.join(base_dir, f"cwnd_{name}.png"))

    def __make_rtt_plot(self, base_dir: str, bw_name: str, experiments: list) -> None:
        """Make a plot indicating the flow RTT over time.

        Parameters
        ----------
        base_dir : str
            The name of the output base directory.
        bw_name : str
            The name of the experiment's bandwidth.
        experiments : list
            A list of experiment names.
        """
        info(
            f"*** Plotting each AQM algorithm's RTT over time: {self.__FLOW_1} - {GROUP_B} - {bw_name}\n"
        )
        plt.figure()
        plt.title("RTT over time")

        for experiment in experiments:
            if experiment != self.__TBF and experiment != self.__SFQ:
                data = pd.read_csv(
                    os.path.join(base_dir, experiment, "hl1", self.__file_formatted),
                    header=None,
                    sep=" ",
                )[:-1][[0, 3]]
                plt.plot(data[0], data[3], label=experiment)

        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.xlabel("time (s)")
        plt.ylabel("RTT (ms)")
        plt.tight_layout()
        plt.savefig(os.path.join(base_dir, "rtt.png"))

    def __make_throughput_plot(
        self,
        base_dir: str,
        bw_name: str,
        colours: np.ndarray,
        experiments: list,
        has_baseline: bool,
        has_sfq_only: bool,
    ) -> None:
        """Make a plot indicating the flow throughput over time.

        Parameters
        ----------
        base_dir : str
            The name of the output base directory.
        bw_name : str
            The name of the experiment's bandwidth.
        colours : numpy.ndarray
            A customised colour map.
        experiments : list
            A list of experiment names.
        has_baseline : bool
            A flag indicating if the baseline should be on the plot.
        has_sfq_only : bool
            A flag indicating if SFQ is the only AQM algorithm on the plot.
        """
        info(
            "*** Plotting "
            + (
                "the baseline and SFQ"
                if has_baseline
                else ("SFQ" if has_sfq_only else "each AQM algorithm")
            )
            + f"'s flow throughput over time: {self.__FLOW_2} - {GROUP_B} - {bw_name}\n"
        )
        plt.figure()
        plt.title(
            f"Throughput over time{'' if has_baseline else ': SFQ'}"
            if has_sfq_only
            else "Fairness"
        )

        for experiment, colour in zip(experiments, colours):
            if (
                (has_baseline and experiment in [self.__TBF, self.__SFQ])
                or (not has_baseline and has_sfq_only and experiment == self.__SFQ)
                or (not has_baseline and not has_sfq_only and experiment != self.__TBF)
            ):
                for i in range(2):
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

        if has_baseline == has_sfq_only:
            plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
            plt.tight_layout()

        plt.xlabel("time (sec)")
        plt.ylabel("throughput (Mbps)")
        plt.savefig(
            os.path.join(
                base_dir,
                "throughput.png"
                if has_baseline
                else ("throughput_sfq.png" if has_sfq_only else "fairness.png"),
            )
        )

    def plot_cwnd(self) -> None:
        """Plot the flow CWND over time for the group transferring data for the specified time length with 1 flow and the default bandwidth."""
        base_dir = os.path.join(
            self.__base_dir, self.__FLOW_1, GROUP_B, self.__BW_NAME_DEFAULT
        )
        experiments = sorted(
            [entry.name for entry in os.scandir(base_dir) if entry.is_dir()]
        )
        colours = plt.cm.jet(np.linspace(0, 1, len(experiments)))

        for name in [self.__CODEL, self.__PIE, self.__RED]:
            self.__make_cwnd_plot(
                base_dir=base_dir, colours=colours, experiments=experiments, name=name
            )

    def plot_fct(self) -> None:
        """Plot all FCT for the group transferring the specified amount of data with 1 flow and the default bandwidth."""
        base_dir = os.path.join(
            self.__base_dir, self.__FLOW_1, GROUP_A, self.__BW_NAME_DEFAULT
        )
        experiments = sorted(
            [entry.name for entry in os.scandir(base_dir) if entry.is_dir()]
        )
        results = [
            pd.read_csv(
                os.path.join(base_dir, experiment, "hl1", self.__file_formatted),
                header=None,
                sep=" ",
            )[-1:][[0]][0]
            for experiment in experiments
        ]
        info(
            f"*** Plotting all FCT: {self.__FLOW_1} - {GROUP_A} - {self.__BW_NAME_DEFAULT}\n"
        )
        plt.figure()
        plt.title("FCT achieved in each experiment")

        for experiment, result in zip(experiments, results):
            plt.bar(experiment, result)

        plt.xlabel("experiment")
        plt.ylabel("FCT (sec)")
        plt.ylim(np.min(results) - 1, np.max(results) + 0.2)
        plt.savefig(os.path.join(base_dir, "fct.png"))

    def plot_rtt(self) -> None:
        """Plot the flow RTT over time for the group transferring data for the specified time length with 1 flow and different bandwidth settings."""
        group_base_dir = os.path.join(self.__base_dir, self.__FLOW_1, GROUP_B)
        bw_names = [
            entry.name for entry in os.scandir(group_base_dir) if entry.is_dir()
        ]

        for bw_name in bw_names:
            base_dir = os.path.join(group_base_dir, bw_name)
            experiments = sorted(
                [
                    entry.name
                    for entry in os.scandir(base_dir)
                    if entry.is_dir() and entry.name != self.__TBF
                ]
            )
            self.__make_rtt_plot(
                base_dir=base_dir, bw_name=bw_name, experiments=experiments
            )

    def plot_throughput(self) -> None:
        """Plot the flow throughput over time for the group transferring data for the same time length with 2 flows and different bandwidth settings."""
        group_base_dir = os.path.join(self.__base_dir, self.__FLOW_2, GROUP_B)
        bw_names = [
            entry.name for entry in os.scandir(group_base_dir) if entry.is_dir()
        ]

        for bw_name in bw_names:
            base_dir = os.path.join(group_base_dir, bw_name)
            experiments = sorted(
                [entry.name for entry in os.scandir(base_dir) if entry.is_dir()]
            )
            colours = plt.cm.jet(np.linspace(0, 1, len(experiments)))

            for has_baseline, has_sfq_only in zip(
                [False, True, False], [True, True, False]
            ):
                self.__make_throughput_plot(
                    base_dir=base_dir,
                    bw_name=bw_name,
                    colours=colours,
                    experiments=experiments,
                    has_baseline=has_baseline,
                    has_sfq_only=has_sfq_only,
                )

    def plot_utilisation(self) -> None:
        """Plot each AQM algorithm's link utilisation for the group transferring data for the specified time length with 1 flow and the default bandwidth."""
        base_dir = os.path.join(
            self.__base_dir, self.__FLOW_1, GROUP_B, self.__BW_NAME_DEFAULT
        )
        experiments = sorted(
            [
                entry.name
                for entry in os.scandir(base_dir)
                if entry.is_dir() and entry.name != self.__TBF
            ]
        )
        results = [
            pd.read_csv(
                os.path.join(base_dir, experiment, "hl1", self.__file_formatted),
                header=None,
                sep=" ",
            )[-1:][[1]][1]
            / 1000
            * 100
            for experiment in experiments
        ]
        info(
            f"*** Plotting each AQM algorithm's link utilisation: {self.__FLOW_1} - {GROUP_B} - {self.__BW_NAME_DEFAULT}\n"
        )
        plt.figure()
        plt.title("Link utilisation")

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
    eval.plot_fct()
    eval.plot_rtt()
    eval.plot_throughput()
    eval.plot_utilisation()
