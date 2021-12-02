"""
'''
Description: the utilities of evaluation
Version: 2.0.0.20211202
Author: Arvin Zhao
Date: 2021-11-21 14:50:13
Last Editors: Arvin Zhao
LastEditTime: 2021-12-02 16:44:19
'''
"""

import os

from mininet.log import info
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from experiment import ARED, BL, CODEL, FQ_CODEL, GROUP_A, GROUP_B, PIE


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
        self.__EXPERIMENTS = [
            BL,
            ARED,
            CODEL,
            FQ_CODEL,
            PIE,
        ]  # A list of the experiment names.
        self.__FLOW_1 = "1f"  # The name of the experiment using 1 flow.
        self.__FLOW_2 = "2f"  # The name of the experiment using 2 flows.
        self.__base_dir = base_dir
        self.__file = file
        self.__file_formatted = file_formatted

    def __label(self, name: str) -> str:
        """Produce the label based on the experiment name.

        Parameters
        ----------
        name : str
            The experiment name.
        """
        if name == CODEL:
            return "CoDel"

        if name == FQ_CODEL:
            return "FQ-CoDel"

        if name == BL:
            return name.capitalize()

        return name.upper()

    def __make_cwnd_plot(self, base_dir: str, name: str) -> None:
        """Make a plot indicating CWND over time.

        Parameters
        ----------
        base_dir : str
            The name of the output base directory.
        name : str
            The name of an experiment for an AQM algorithm to compare with the baseline.
        """
        info(
            f"*** Plotting the baseline and the AQM algorithm's CWND over time: {self.__FLOW_1} - {GROUP_B} - {self.__BW_NAME_DEFAULT} - {name}\n"
        )
        plt.figure()
        plt.title(f"CWND over time: {self.__label(name=name)}")

        for experiment, colour in zip(
            self.__EXPERIMENTS, plt.cm.jet(np.linspace(0, 1, len(self.__EXPERIMENTS)))
        ):
            if experiment == BL or experiment == name:
                data = pd.read_csv(
                    os.path.join(base_dir, experiment, "hl1", self.__file_formatted),
                    header=None,
                    sep=" ",
                )[:-1][[0, 2]]
                plt.plot(
                    data[0], data[2], color=colour, label=self.__label(name=experiment)
                )

        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.xlabel("time (sec)")
        plt.ylabel("CWND (MB)")
        plt.tight_layout()
        plt.savefig(os.path.join(base_dir, f"cwnd_{name}.png"))

    def __make_rtt_plot(self, base_dir: str, bw_name: str) -> None:
        """Make a plot indicating RTT over time.

        Parameters
        ----------
        base_dir : str
            The name of the output base directory.
        bw_name : str
            The name of the experiment's bandwidth.
        """
        info(f"*** Plotting RTT over time: {self.__FLOW_1} - {GROUP_B} - {bw_name}\n")
        plt.figure()
        plt.title("RTT over time")

        for experiment in self.__EXPERIMENTS:
            data = pd.read_csv(
                os.path.join(base_dir, experiment, "hl1", self.__file_formatted),
                header=None,
                sep=" ",
            )[:-1][[0, 3]]
            plt.plot(data[0], data[3], label=self.__label(name=experiment))

        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.xlabel("time (s)")
        plt.ylabel("RTT (ms)")
        plt.tight_layout()
        plt.savefig(os.path.join(base_dir, "rtt.png"))

    def plot_cwnd(self) -> None:
        """Plot CWND over time for the group transferring data for the specified time length with 1 flow and the default bandwidth."""
        base_dir = os.path.join(
            self.__base_dir, self.__FLOW_1, GROUP_B, self.__BW_NAME_DEFAULT
        )

        for name in self.__EXPERIMENTS:
            if name != BL:
                self.__make_cwnd_plot(base_dir=base_dir, name=name)

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
        results = [
            pd.read_csv(
                os.path.join(base_dir, experiment, "hl1", self.__file_formatted),
                header=None,
                sep=" ",
            )[-1:][[0]][0]
            for experiment in self.__EXPERIMENTS
        ]
        info(
            f"*** Plotting FCT: {self.__FLOW_1} - {group} - {self.__BW_NAME_DEFAULT}\n"
        )
        plt.figure()
        plt.title("FCT achieved in each experiment")

        for experiment, result in zip(self.__EXPERIMENTS, results):
            plt.bar(self.__label(name=experiment), result)

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
        results = []

        for experiment in self.__EXPERIMENTS:
            lines = open(
                os.path.join(base_dir, experiment, "s1-eth2", self.__file), "r"
            ).readlines()
            retransmissions = [line for line in lines if "Retransmission" in line]
            results.append(len(retransmissions) / len(lines) * 100)

        info(f"*** Plotting RR: {self.__FLOW_1} - {group} - {self.__BW_NAME_DEFAULT}\n")
        plt.figure()
        plt.title("RR achieved in each experiment")

        for experiment, result in zip(self.__EXPERIMENTS, results):
            plt.bar(self.__label(name=experiment), result)

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
            self.__make_rtt_plot(base_dir=base_dir, bw_name=bw_name)

    def plot_throughput(self) -> None:
        """Plot throughput over time for the group transferring data for the same time length with 2 flows and the default bandwidth."""
        base_dir = os.path.join(
            self.__base_dir, self.__FLOW_2, GROUP_B, self.__BW_NAME_DEFAULT
        )
        info(
            f"*** Plotting throughput over time: {self.__FLOW_2} - {GROUP_B} - {self.__BW_NAME_DEFAULT}\n"
        )
        plt.figure()
        plt.title("Fairness")

        for experiment, colour in zip(
            self.__EXPERIMENTS, plt.cm.jet(np.linspace(0, 1, len(self.__EXPERIMENTS)))
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
                    label=self.__label(name=experiment) if i == 0 else None,
                )

        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.xlabel("time (sec)")
        plt.ylabel("throughput (Mbps)")
        plt.tight_layout()
        plt.savefig(os.path.join(base_dir, "fairness.png"))

    def plot_utilisation(self) -> None:
        """Plot link utilisation for the group transferring data for the specified time length with 1 flow and the default bandwidth."""
        base_dir = os.path.join(
            self.__base_dir, self.__FLOW_1, GROUP_B, self.__BW_NAME_DEFAULT
        )
        experiments = [
            experiment for experiment in self.__EXPERIMENTS if experiment != BL
        ]
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
        results_min = np.min(results)
        results_min = results_min if results_min < 90 else 90
        info(
            f"*** Plotting link utilisation: {self.__FLOW_1} - {GROUP_B} - {self.__BW_NAME_DEFAULT}\n"
        )
        plt.figure()
        plt.title("Link utilisation")

        for experiment, result in zip(experiments, results):
            plt.bar(self.__label(name=experiment), result)

        plt.axhline(y=90, color="k", linestyle="-")
        plt.ylabel("link utilisation (%)")
        plt.ylim(results_min - 5, 100)
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
