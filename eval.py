"""
'''
Description: the utilities of evaluation
Version: 2.0.0.20211127
Author: Arvin Zhao
Date: 2021-11-21 14:50:13
Last Editors: Arvin Zhao
LastEditTime: 2021-11-27 00:59:13
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

    def __init__(self, base_dir: str, file: str, file_formatted: str) -> None:
        """The constructor of the class for defining the utilities of evaluation.

        Parameters
        ----------
        base_dir : str
            The name of the output base directory.
        file : str
            The filename with the file extension of the output file.
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
        self.__file = file
        self.__file_formatted = file_formatted

    def __make_cwnd_plot(
        self, base_dir: str, colours: np.ndarray, experiments: list, name: str
    ) -> None:
        """Make a plot indicating CWND over time.

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
            f"*** Plotting the baseline and the AQM algorithm's CWND over time: {self.__FLOW_1} - {GROUP_B} - {self.__BW_NAME_DEFAULT} - {name}\n"
        )
        plt.figure()
        plt.title(
            f"CWND over time: {'CoDel' if name == self.__CODEL else name.upper()}"
        )

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
        """Make a plot indicating RTT over time.

        Parameters
        ----------
        base_dir : str
            The name of the output base directory.
        bw_name : str
            The name of the experiment's bandwidth.
        experiments : list
            A list of experiment names.
        """
        info(f"*** Plotting RTT over time: {self.__FLOW_1} - {GROUP_B} - {bw_name}\n")
        plt.figure()
        plt.title("RTT over time")

        for experiment in experiments:
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
        has_sfq_only: bool,
    ) -> None:
        """Make a plot indicating throughput over time.

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
        has_sfq_only : bool
            A flag indicating if SFQ is the only AQM algorithm on the plot.
        """
        info(
            "*** Plotting "
            + ("the baseline and SFQ's " if has_sfq_only else "")
            + f"throughput over time: {self.__FLOW_2} - {GROUP_B} - {bw_name}"
            + (f" - {self.__SFQ}" if has_sfq_only else "")
            + "\n"
        )
        plt.figure()
        plt.title(
            f"Throughput over time: {self.__SFQ.upper()}"
            if has_sfq_only
            else "Fairness"
        )

        for experiment, colour in zip(experiments, colours):
            if (
                has_sfq_only and experiment in [self.__SFQ, self.__TBF]
            ) or not has_sfq_only:
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

        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.xlabel("time (sec)")
        plt.ylabel("throughput (Mbps)")
        plt.tight_layout()
        plt.savefig(
            os.path.join(
                base_dir,
                f"throughput_{self.__SFQ}.png" if has_sfq_only else "fairness.png",
            ),
        )

    def plot_cwnd(self) -> None:
        """Plot CWND over time for the group transferring data for the specified time length with 1 flow and the default bandwidth."""
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

    def plot_fct(self, group_suffix: str = "") -> None:
        """Plot FCT for the group transferring the specified amount of data with 1 flow and the default bandwidth.

        Parameters
        ----------
        group_suffix : str, optional
            The suffix added to the experiment group for the output directory (the default is an empty string).
        """
        group = GROUP_A + group_suffix
        base_dir = os.path.join(
            self.__base_dir, self.__FLOW_1, group, self.__BW_NAME_DEFAULT
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
            f"*** Plotting FCT: {self.__FLOW_1} - {group} - {self.__BW_NAME_DEFAULT}\n"
        )
        plt.figure()
        plt.title("FCT achieved in each experiment")

        for experiment, result in zip(experiments, results):
            plt.bar(experiment, result)

        plt.xlabel("experiment")
        plt.ylabel("FCT (sec)")
        plt.ylim(np.min(results) - 1, np.max(results) + 0.2)
        plt.savefig(os.path.join(base_dir, "fct.png"))

    def plot_rr(self, group_suffix: str = "") -> None:
        """Plot RR for the group transferring the specified amount of data with 1 flow and the default bandwidth.

        Parameters
        ----------
        group_suffix : str, optional
            The suffix added to the experiment group for the output directory (the default is an empty string).
        """
        group = GROUP_A + group_suffix
        base_dir = os.path.join(
            self.__base_dir, self.__FLOW_1, group, self.__BW_NAME_DEFAULT
        )
        experiments = sorted(
            [entry.name for entry in os.scandir(base_dir) if entry.is_dir()]
        )
        results = []

        for experiment in experiments:
            lines = open(
                os.path.join(base_dir, experiment, "s1-eth2", self.__file), "r"
            ).readlines()
            retransmissions = [line for line in lines if "Retransmission" in line]
            results.append(len(retransmissions) / len(lines) * 100)

        info(f"*** Plotting RR: {self.__FLOW_1} - {group} - {self.__BW_NAME_DEFAULT}\n")
        plt.figure()
        plt.title("RR achieved in each experiment")

        for experiment, result in zip(experiments, results):
            plt.bar(experiment, result)

        plt.xlabel("experiment")
        plt.ylabel("RR (%)")
        plt.savefig(os.path.join(base_dir, "rr.png"))

    def plot_rtt(self) -> None:
        """Plot RTT over time for the group transferring data for the specified time length with 1 flow and different bandwidth settings."""
        group_base_dir = os.path.join(self.__base_dir, self.__FLOW_1, GROUP_B)
        bw_names = [
            entry.name for entry in os.scandir(group_base_dir) if entry.is_dir()
        ]

        for bw_name in bw_names:
            base_dir = os.path.join(group_base_dir, bw_name)
            experiments = sorted(
                [entry.name for entry in os.scandir(base_dir) if entry.is_dir()]
            )
            self.__make_rtt_plot(
                base_dir=base_dir, bw_name=bw_name, experiments=experiments
            )

    def plot_throughput(self) -> None:
        """Plot throughput over time for the group transferring data for the same time length with 2 flows and different bandwidth settings."""
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

            for has_sfq_only in [True, False]:
                if not has_sfq_only and bw_name != self.__BW_NAME_DEFAULT:
                    continue

                self.__make_throughput_plot(
                    base_dir=base_dir,
                    bw_name=bw_name,
                    colours=colours,
                    experiments=experiments,
                    has_sfq_only=has_sfq_only,
                )

    def plot_utilisation(self) -> None:
        """Plot link utilisation for the group transferring data for the specified time length with 1 flow and the default bandwidth."""
        base_dir = os.path.join(
            self.__base_dir, self.__FLOW_1, GROUP_B, self.__BW_NAME_DEFAULT
        )
        experiments = sorted(
            [entry.name for entry in os.scandir(base_dir) if entry.is_dir()]
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
            f"*** Plotting link utilisation: {self.__FLOW_1} - {GROUP_B} - {self.__BW_NAME_DEFAULT}\n"
        )
        plt.figure()
        plt.title("Link utilisation")

        for experiment, result in zip(experiments, results):
            plt.bar(experiment, result)

        plt.xlabel("experiment")
        plt.ylabel("link utilisation (%)")
        plt.ylim(np.min(results) - 5, 100)
        plt.savefig(os.path.join(base_dir, "utilisation.png"))


# Simple test purposes only.
if __name__ == "__main__":
    from mininet.log import setLogLevel
    from experiment import OUTPUT_BASE_DIR, OUTPUT_FILE, OUTPUT_FILE_FORMATTED

    group_suffix = "_sp"
    setLogLevel("info")
    eval = Eval(
        base_dir=OUTPUT_BASE_DIR, file=OUTPUT_FILE, file_formatted=OUTPUT_FILE_FORMATTED
    )
    eval.plot_cwnd()
    eval.plot_fct()
    eval.plot_fct(group_suffix=group_suffix)
    eval.plot_rr(group_suffix=group_suffix)
    eval.plot_rtt()
    eval.plot_throughput()
    eval.plot_utilisation()
