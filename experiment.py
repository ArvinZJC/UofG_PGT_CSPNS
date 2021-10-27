"""
'''
Description: the utilities of the experiment settings
Version: 1.0.0.20211026
Author: Arvin Zhao
Date: 2021-10-18 12:03:55
Last Editors: Arvin Zhao
LastEditTime: 2021-10-27 15:50:16
'''
"""

from datetime import datetime
from math import ceil
from multiprocessing import Process
from shutil import rmtree
from subprocess import PIPE, Popen
import os

from mininet.log import error, info, warning
from mininet.util import quietRun

from eval import plot_rtt, plot_throughput
from errors import BadCmdError, PoorPrepError
from net import Net

OUTPUT_BASE_DIR = "output"
OUTPUT_FILE = "result.txt"
OUTPUT_FILE_FORMATTED = "result_new.txt"


class Experiment:
    """The class for defining the utilities of the experiment settings."""

    def __init__(self, rtt: int = 20) -> None:
        """The constructor of the class for defining the utilities of the experiment settings.

        Parameters
        ----------
        rtt : int, optional
            The round-trip time (RTT) latency in milliseconds (the default is 20).

        Raises
        ------
        ValueError
            The value for RTT is invalid. Set a value larger than 0 but no larger than 4294967.
        """
        self.__CLIENT = "client"  # The displayed name of the client in the outputs.
        self.__QDISC = ["tbf"]  # A list of the supported classlist queueing disciplines.
        self.__bdp = None
        self.__mn = Net()

        # No longer than the max time value of the Linux command `tc`.
        if rtt <= 0 and rtt > 4294967:
            raise ValueError("invalid RTT value")

        self.__rtt = rtt

    def __apply_qdisc(
        self, bw: int, bw_unit: str, limit: int, qdisc: str = "tbf"
    ) -> None:
        """Apply a classless queueing discipline.

        Support Token Bucket Filter (TBF) TODO.

        Parameters
        ----------
        bw : int
            The bandwidth.
        bw_unit : str
            The bandwidth unit.
        limit : int
            For TBF, the number of bytes that can be queued waiting for tokens to become available.
        qdisc : str, optional
            A classless queueing discipline (the default is "tbf", and the other accepted values are TODO).

        Raises
        ------
        BadCmdError
            The executed command fails, so the classless queueing discipline is not applied. Check the command.
        ValueError
            The classless queueing discipline is invalid. Check if it is one of the supported ones.
        """
        qdisc = qdisc.lower().strip()

        if qdisc not in self.__QDISC:
            raise ValueError("invalid classless queueing discipline")

        info(f"*** Applying {qdisc.upper()}\n")
        cmd = "tc qdisc add dev s1-eth2 "  # Apply the discipline on s1-eth2 to affect the right part of the tree topology.

        if qdisc == "tbf":
            hz = int(
                Popen(
                    "egrep '^CONFIG_HZ_[0-9]+' /boot/config-`uname -r`",
                    shell=True,
                    stdout=PIPE,
                )
                .stdout.read()
                .decode()
                .replace("CONFIG_HZ_", "")
                .replace("=y\n", "")
            )
            burst = int(
                bw * (1000000000 if bw_unit == "gbit" else 1000000) / hz / 8
            )  # Reference: https://unix.stackexchange.com/a/100797
            cmd += (
                f"root handle 1: {qdisc} burst {burst} limit {limit} rate {bw}{bw_unit}"
            )
        else:
            cmd += f"parent 1: handle 2: {qdisc} "
            # TODO:

        info(f'*** {self.__CLIENT} : ("{cmd}")\n')

        if not os.WIFEXITED(os.system(cmd)):
            raise BadCmdError

    def __check_bw_unit(self, bw_unit: str) -> str:
        """Check if the bandwidth unit is one of "gbit" and "mbit".

        Parameters
        ----------
        bw_unit : str
            The bandwidth unit.

        Returns
        -------
        str
            The bandwidth unit changing to lowercase letters and removing extra spaces.

        Raises
        ------
        ValueError
            The bandwidth unit is invalid. Check if the value is one of "gbit" and "mbit".
        """
        bw_unit = bw_unit.lower().strip()

        if bw_unit not in ["gbit", "mbit"]:
            raise ValueError("invalid bandwidth unit")

        return bw_unit

    def __create_output_dir(self) -> None:
        """Create the hosts' output directories."""
        info("*** Creating the hosts' output directories if they do not exist\n")

        for host in self.__mn.net.hosts:
            output_dir = os.path.join(OUTPUT_BASE_DIR, host.name)

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

    def __format_output(self) -> None:
        """Format the client hosts' output files."""
        info("*** Formatting the client hosts' output files\n")

        for i in [0, 1]:
            self.__mn.net.hosts[i].cmdPrint(
                "cat "
                + os.path.join(OUTPUT_BASE_DIR, f"h{i + 1}", OUTPUT_FILE)
                + "| grep sec | tr - ' ' | tr / ' ' | awk '{print $4,$8,$15}' > "
                + os.path.join(OUTPUT_BASE_DIR, f"h{i + 1}", OUTPUT_FILE_FORMATTED)
            )

    def __iperf_client(self, client_idx: int, time: int) -> None:
        """A multiprocessing task to run an iPerf client.

        Parameters
        ----------
        client_idx : int
            The index of the client host.
        time : int
            The time in seconds for running an iPerf client.
        """
        cmd = (
            f"iperf -c {self.__mn.net.hosts[client_idx + 2].IP()} -i 1 -t {time} -e > "
            + os.path.join(OUTPUT_BASE_DIR, f"h{client_idx + 1}", OUTPUT_FILE)
        )
        info(f'*** h{client_idx + 1} : ("{cmd}")\n')
        info(f"It starts at {datetime.now()} and should last for {time} second(s).\n")
        self.__mn.net.hosts[client_idx].cmd(cmd)

    def __launch_servers(self) -> None:
        """Launch iPerf in the server mode in the background."""
        info("*** Launching iPerf in the server mode in the background\n")

        # h3 and h4.
        for i in [2, 3]:
            self.__mn.net.hosts[i].cmdPrint(
                "iperf -i 1 -s > "
                + os.path.join(OUTPUT_BASE_DIR, f"h{i + 1}", OUTPUT_FILE)
                + " &"
            )  # Add "&" in the end to run in the background.

    def __run_clients(self, time: int) -> None:
        """Run iPerf clients almost simultaneously.

        Parameters
        ----------
        time : int
            The time in seconds for running an iPerf client.
        """
        info("*** Running iPerf clients almost simultaneously\n")
        processes = []

        # h1 and h2.
        for i in [0, 1]:
            process = Process(target=self.__iperf_client, args=(i, time))
            processes.append(process)
            process.start()

        for process in processes:
            process.join()

    def __set_delay(self) -> None:
        """Emulate high-latency WAN.

        Raises
        ------
        BadCmdError
            The executed command fails, so the delay cannot be set. Check the command.
        """
        info("*** Emulating high-latency WAN\n")
        self.__mn.net.hosts[0].cmdPrint("ping -c 4", self.__mn.net.hosts[2].IP())
        cmd = f"tc qdisc add dev s2-eth3 root netem delay {self.__rtt}ms"  # Set the delay on s2-eth3 to affect h1 and h2.
        info(f'*** {self.__CLIENT} : ("{cmd}")\n')

        if not os.WIFEXITED(os.system(cmd)):
            raise BadCmdError

        # Validation.
        self.__mn.net.hosts[0].cmdPrint("ping -c 4", self.__mn.net.hosts[2].IP())
        self.__mn.net.hosts[1].cmdPrint("ping -c 4", self.__mn.net.hosts[2].IP())

    def __set_host_buffer(self) -> None:
        """Set the hosts' buffer size."""
        info("*** Setting the hosts' buffer size\n")

        for host in self.__mn.net.hosts:
            host.cmdPrint(
                f"sysctl -w net.ipv4.tcp_rmem='10240 87380 {20 * self.__bdp}'"
            )  # Buffer size: 'minimum default maximum (20·BDP)'.
            host.cmdPrint(
                f"sysctl -w net.ipv4.tcp_wmem='10240 87380 {20 * self.__bdp}'"
            )

    def clear_output(self) -> None:
        """Clear the output directory."""
        try:
            if os.path.isdir(OUTPUT_BASE_DIR):
                rmtree(path=OUTPUT_BASE_DIR)
                info("*** Clearing the output directory\n")
        except Exception as e:
            error(str(e) + "\n")
            warning("You may need to clear the output directory manually.\n")

    def do(
        self,
        aqm: str = None,
        bw: int = 1,
        bw_unit: str = "gbit",
        has_clean_lab: bool = False,
        time: int = 30,
    ) -> None:
        """Do an experiment.

        Parameters
        ----------
        aqm : str, optional
            A classless queueing discipline representing an AQM algorithm (the default is `None`).
        bw : int, optional
            The bandwidth (the default is 1).
        bw_unit : str, optional
            The bandwidth unit (the default is "gbit", and "mbit" is another accepted value).
        has_clean_lab : bool, optional
            A flag indicating if the junk should be cleaned up to avoid any potential error before creating the simulated network (the default is `False`).
        time : int, optional
            The time in seconds for running an iPerf client (the default is 30).

        Raises
        ------
        PoorPrepError
            BDP is not set. Check the call to the function `set_bdp()` before this function.
        """
        bw_unit = self.__check_bw_unit(bw_unit=bw_unit)

        if self.__bdp is None:
            raise PoorPrepError(message="BDP not set")

        if time <= 0:
            time = 30
            warning(
                "Invalid time in seconds for running an iPerf client. The experiment default is used instead.\n"
            )

        self.__mn.start(has_clean_lab=has_clean_lab)
        self.__set_delay()
        self.__set_host_buffer()
        self.__apply_qdisc(bw=bw, bw_unit=bw_unit, limit=10 * self.__bdp)  # Apply TBF.
        # TODO: AQM
        self.__create_output_dir()
        self.__launch_servers()
        self.__run_clients(time=time)
        quietRun("killall -9 iperf")  # Shut down any iPerf that might still be running.
        self.__format_output()
        plot_rtt()
        plot_throughput()
        self.__mn.stop()

    def set_bdp(self, bw: int = 1, bw_unit: str = "gbit") -> None:
        """Set the bandwidth-delay product (BDP).

        Parameters
        ----------
        bw : int, optional
            The bandwidth for determining BDP (the default is 1).
        bw_unit : str, optional
            The bandwidth unit (the default is "gbit", and "mbit" is another accepted value).

        Raises
        ------
        ValueError
            The bandwidth unit is invalid. Check if the value is one of "gbit" and "mbit".
        """
        bw_unit = self.__check_bw_unit(bw_unit=bw_unit)
        self.__bdp = (
            bw * (1000000000 if bw_unit == "gbit" else 1000000) * self.__rtt / 1000 / 8
        )  # BDP (byte) = BW (bit/second) × RTT (second) / 8

        # Make BDP divisible by 1024.
        if self.__bdp % 1024 != 0:
            self.__bdp = ceil(self.__bdp / 1024) * 1024

        # BDP would not be smaller than the default buffer allocated when applications create a TCP socket.
        if self.__bdp < 87380:
            self.__bdp = 87380
