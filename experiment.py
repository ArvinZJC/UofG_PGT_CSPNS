"""
'''
Description: the utilities of the experiment settings
Version: 1.0.0.20211101
Author: Arvin Zhao
Date: 2021-10-18 12:03:55
Last Editors: Arvin Zhao
LastEditTime: 2021-11-01 17:59:42
'''
"""

from datetime import datetime
from math import ceil
from multiprocessing import Process
from shutil import rmtree
from subprocess import check_call, DEVNULL, PIPE, Popen, STDOUT
from time import sleep
import os

from mininet.log import error, info, warning
from mininet.util import quietRun

from eval import (
    OUTPUT_BASE_DIR,
    OUTPUT_FILE,
    OUTPUT_FILE_FORMATTED,
    plot_rtt,
    plot_throughput,
)
from errors import PoorPrepError
from net import Net

ALPHA_DEFAULT = 2
BETA_DEFAULT = 25


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
        self.__QDISC = [
            "codel",
            "pie",
            "red",
            "sfq",
            "tbf",
        ]  # A list of the supported classlist queueing disciplines.
        self.__bdp = None
        self.__mn = Net()

        # No longer than the max time value of the Linux command `tc`.
        if rtt <= 0 and rtt > 4294967:
            raise ValueError("invalid RTT value")

        self.__rtt = rtt
        self.__suboutput = None  # The output folder name of an experiment group.

    def __apply_qdisc(
        self,
        alpha: int,
        avpkt: int,
        beta: int,
        bw: int,
        bw_unit: str,
        interval: int,
        limit: int,
        perturb: int,
        target: int,
        tupdate: int,
        qdisc: str = "tbf",
    ) -> None:
        """Apply a classless queueing discipline.

        Support Controlled Delay (CoDel), Stochastic Fair Queueing (SFQ), Random Early Detection (RED), Token Bucket Filter (TBF), and Proportional Integral Controller-Enhanced (PIE).

        Parameters
        ----------
        alpha : int
            A smaller parameter for PIE to control the drop probability.
        avpkt : int
            A parameter for RED used with the burst to determine the time constant for average queue size calculations.
        beta : int
            A larger parameter for PIE to control the drop probability.
        bw : int
            The bandwidth.
        bw_unit : str
            The bandwidth unit.
        interval : int
            A value in milliseconds for CoDel to ensure that the measured minimum delay does not become too stale.
        limit : int
            For CoDel and PIE, the limit on the queue size in packets.
            For TBF, the number of bytes that can be queued waiting for tokens to become available.
        perturb : int
            The interval in seconds for the queue algorithm perturbation in SFQ.
        target : int
            For CoDel, the acceptable minimum standing/persistent queue delay in milliseconds.
            For PIE, the expected queue delay in milliseconds.
        tupdate : int
            The frequency in milliseconds for PIE at which the system drop probability is calculated.
        qdisc : str, optional
            A classless queueing discipline (the default is "tbf").

        Raises
        ------
        BadCmdError
            The executed command fails, so the classless queueing discipline is not applied. Check the command.
        ValueError
            The classless queueing discipline is invalid. Check if it is one of the supported ones.
        """
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

            if qdisc == "codel":
                cmd += f"limit {limit} interval {interval}ms target {target}ms"
            elif qdisc == "pie":
                cmd += f"alpha {alpha} beta {beta} limit {limit} target {target}ms tupdate {tupdate}ms"
            elif qdisc == "red":
                # Reference: https://man7.org/linux/man-pages/man8/tc-red.8.html
                max = int(limit / 4)
                min = int(max / 3)
                burst = int((2 * min + max) / (3 * avpkt))
                cmd += f"adaptative avpkt {avpkt} bandwidth {bw}{bw_unit} burst {burst} limit {limit} max {max} min {min}"
            else:
                cmd += f"perturb {perturb}"

        info(f'*** {self.__CLIENT} : ("{cmd}")\n')
        check_call(cmd, shell=True)

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
        """Create the output directories."""
        info("*** Creating the output directories if they do not exist\n")
        sections = [host.name for host in self.__mn.net.hosts]
        sections.extend(["s2-eth1", "s2-eth2"])

        for section in sections:
            output_dir = os.path.join(OUTPUT_BASE_DIR, self.__suboutput, section)

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

    def __format_output(self) -> None:
        """Format the client hosts' output files."""
        info("*** Formatting the client hosts' output files\n")

        for i in [0, 1]:
            self.__mn.net.hosts[i].cmdPrint(
                "cat "
                + os.path.join(
                    OUTPUT_BASE_DIR, self.__suboutput, f"h{i + 1}", OUTPUT_FILE
                )
                + "| grep sec | tr - ' ' | tr / ' ' | awk '{print $4,$8,$15}' > "
                + os.path.join(
                    OUTPUT_BASE_DIR,
                    self.__suboutput,
                    f"h{i + 1}",
                    OUTPUT_FILE_FORMATTED,
                )
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
            + os.path.join(
                OUTPUT_BASE_DIR, self.__suboutput, f"h{client_idx + 1}", OUTPUT_FILE
            )
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
                + os.path.join(
                    OUTPUT_BASE_DIR, self.__suboutput, f"h{i + 1}", OUTPUT_FILE
                )
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

    def __run_wireshark(self) -> None:
        """Run Wireshark (TShark) in the background."""
        info("*** Running Wireshark (TShark) in the background\n")
        processes = []

        # s2-eth1 for h1 and s2-eth2 for h2.
        for i in [1, 2]:
            process = Process(target=self.__wireshark, args=(i,))
            processes.append(process)
            process.start()

        for process in processes:
            process.join()

        sleep(1)  # Wait for 1 second to ensure full capture.

    def __set_delay(self) -> None:
        """Emulate high-latency WAN.

        Raises
        ------
        BadCmdError
            The executed command fails, so the delay cannot be set. Check the command.
        """
        info("*** Emulating high-latency WAN\n")
        ping = "ping -c 4"
        self.__mn.net.hosts[0].cmdPrint(ping, self.__mn.net.hosts[2].IP())
        cmd = f"tc qdisc add dev s2-eth3 root netem delay {self.__rtt}ms"  # Set the delay on s2-eth3 to affect h1 and h2.
        info(f'*** {self.__CLIENT} : ("{cmd}")\n')
        check_call(cmd, shell=True)

        # Validation.
        self.__mn.net.hosts[0].cmdPrint(ping, self.__mn.net.hosts[2].IP())
        self.__mn.net.hosts[1].cmdPrint(ping, self.__mn.net.hosts[2].IP())

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

    def __wireshark(self, s_eth_idx: int) -> None:
        """A multiprocessing task to run Wireshark (TShark).

        Parameters
        ----------
        s_eth_idx : int
            The index of a switch's interface.
        """
        s_eth = f"s2-eth{s_eth_idx}"
        cmd = f"tshark -f 'tcp' -i {s_eth} > {os.path.join(OUTPUT_BASE_DIR, self.__suboutput, s_eth, OUTPUT_FILE)} &"
        check_call(cmd, shell=True, stderr=STDOUT, stdout=DEVNULL)
        info(f'*** {s_eth} : ("{cmd}")\n')
        info(f"It starts at {datetime.now()}.\n")

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
        name: str,
        alpha: int = ALPHA_DEFAULT,
        avpkt: int = 1000,
        aqm: str = None,
        beta: int = BETA_DEFAULT,
        bw: int = 1,
        bw_unit: str = "gbit",
        has_clean_lab: bool = False,
        interval: int = 100,
        limit: int = 1000,
        perturb: int = 10,
        target: int = 5,
        time: int = 30,
        tupdate: int = 15,
    ) -> None:
        """Do an experiment.

        Parameters
        ----------
        name : int
            The experiment name.
        alpha : int, optional
            A smaller parameter for PIE to control the drop probability (the default is defined by a constant `ALPHA_DEFAULT`, and the value should be in the range between 0 and 32).
        aqm : str, optional
            A classless queueing discipline representing an AQM algorithm (the default is `None`).
        avpkt : int, optional
            A parameter for RED used with the burst to determine the time constant for average queue size calculations (the default is 1000).
        beta : int, optional
            A larger parameter for PIE to control the drop probability (the default is defined by a constant `BETA_DEFAULT`, and the value should be in the range between 0 and 32).
        bw : int, optional
            The bandwidth (the default is 1).
        bw_unit : str, optional
            The bandwidth unit (the default is "gbit", and "mbit" is another accepted value).
        has_clean_lab : bool, optional
            A flag indicating if the junk should be cleaned up to avoid any potential error before creating the simulated network (the default is `False`).
        interval : int, optional
            A value in milliseconds for CoDel to ensure that the measured minimum delay does not become too stale (the default is 100).
        limit : int, optional
            For CoDel and PIE, the limit on the queue size in packets (the default is 1000).
            For TBF, the number of bytes that can be queued waiting for tokens to become available (the default is not for this case).
        perturb : int, optional
            The interval in seconds for the queue algorithm perturbation in SFQ (the default is 10).
        target : int, optional
            For CoDel, the acceptable minimum standing/persistent queue delay in milliseconds (the default is 5).
            For PIE, the expected queue delay in milliseconds (the default is not for this case).
        time : int, optional
            The time in seconds for running an iPerf client (the default is 30).
        tupdate : int, optional
            The frequency in milliseconds for PIE at which the system drop probability is calculated (the default is 15).

        Raises
        ------
        PoorPrepError
            BDP is not set. Check the call to the function `set_bdp()` before this function.
        """
        bw_unit = self.__check_bw_unit(bw_unit=bw_unit)

        if self.__bdp is None:
            raise PoorPrepError(message="BDP not set")

        if alpha >= beta or alpha < 0 or alpha > 32 or beta < 0 or beta > 32:
            alpha = ALPHA_DEFAULT
            beta = BETA_DEFAULT
            warning(
                "Invalid alpha and beta for PIE. The experiment defaults are used instead.\n"
            )

        info(f"****** Starting the experiment: {name}\n")
        self.__mn.start(has_clean_lab=has_clean_lab)
        self.__set_delay()
        self.__set_host_buffer()
        self.__apply_qdisc(
            alpha=alpha,
            avpkt=avpkt,
            beta=beta,
            bw=bw,
            bw_unit=bw_unit,
            interval=interval,
            limit=10 * self.__bdp,
            perturb=perturb,
            target=target,
            tupdate=tupdate,
        )  # Apply TBF.
        self.__suboutput = "baseline"

        if aqm is not None:
            aqm = aqm.lower().strip()

            if aqm != "tbf":
                self.__apply_qdisc(
                    alpha=alpha,
                    avpkt=avpkt,
                    beta=beta,
                    bw=bw,
                    bw_unit=bw_unit,
                    interval=interval,
                    limit=limit,
                    perturb=perturb,
                    qdisc=aqm,
                    target=target,
                    tupdate=tupdate,
                )
                self.__suboutput = aqm

        self.__create_output_dir()
        self.__run_wireshark()
        self.__launch_servers()
        self.__run_clients(time=time)
        quietRun(
            "killall -15 tshark"
        )  # Softly terminate any TShark that might still be running. Put the code here to reduce useless capture.
        quietRun(
            "killall -9 iperf"
        )  # Immediately terminate any iPerf that might still be running.
        self.__format_output()
        info("*** Plotting RTT over time\n")
        plot_rtt(suboutput=self.__suboutput)
        info("*** Plotting throughput over time\n")
        plot_throughput(suboutput=self.__suboutput)
        self.__mn.stop()
        info("\n")

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
