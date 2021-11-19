"""
'''
Description: the utilities of the experiment settings
Version: 2.0.0.20211119
Author: Arvin Zhao
Date: 2021-11-18 12:03:55
Last Editors: Arvin Zhao
LastEditTime: 2021-11-19 19:36:53
'''
"""

from datetime import datetime
from math import ceil, floor
from multiprocessing import Process
from shutil import rmtree
from subprocess import check_call, DEVNULL, PIPE, Popen, STDOUT
from time import sleep
import os

from mininet.log import error, info, warning
from mininet.util import quietRun

from errors import PoorPrepError
from net import check_bw_unit, Net

ALPHA_DEFAULT = 2
BETA_DEFAULT = 25
N_B_UNIT_DEFAULT = "M"
OUTPUT_BASE_DIR = "output"  # The name of the output base directory.
SUMMARY_FILE = (
    "summary.txt"  # The filename with the file extension of the summary file.
)


class Experiment:
    """The class for defining the utilities of the experiment settings."""

    def __init__(self, has_capture: bool = False) -> None:
        """The constructor of the class for defining the utilities of the experiment settings.

        Parameters
        ----------
        has_capture : bool, optional
            A flag indicating if the PCAPNG capture file from Wireshark (TShark) should be generated (the default is `False`, and the disk space should be sufficient if the parameter is set to `True`).
        Raises
        ------
        ValueError
            The value for RTT is invalid. Set a value larger than 0 but no larger than 4294967.
        """
        self.__CAPTURE_FILE = (
            "result.pcapng"  # The filename with the file extension of the capture file.
        )
        self.__CLIENT = "client"  # The displayed name of the client in the outputs.
        self.__N_B_UNITS = {
            0: "G",
            1: "K",
            2: "M",
        }  # The dictionary of the units of the number of bytes transferred from an iPerf client.
        self.__OUTPUT_FILE = (
            "result.txt"  # The filename with the file extension of the output file.
        )
        self.__OUTPUT_FILE_FORMATTED = "result_new.txt"  # The filename with the file extension of the formatted output file.
        self.__QDISC = [
            "codel",
            "pie",
            "red",
            "sfq",
            "tbf",
        ]  # A list of the supported classlist queueing disciplines.
        self.__bdp = None
        self.__group = None  # The output folder name using the experiment group name.
        self.__has_capture = has_capture
        self.__mn = Net()
        self.__n_hosts = 0  # The number of hosts.
        self.__name = None  # The output folder name using the experiment name.

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
            For RED, the limit on the queue size in bytes.
            For TBF, the number of bytes that can be queued waiting for tokens to become available.
        perturb : int
            The interval in seconds for the queue algorithm perturbation in SFQ.
        qdisc : str
            A classless queueing discipline.
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
        cmd = "tc qdisc add dev s1-eth1 "

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
                # References:
                # 1. https://man7.org/linux/man-pages/man8/tc-red.8.html
                # 2. http://www.fifi.org/doc/HOWTO/en-html/Adv-Routing-HOWTO-14.html - Section 14.5
                min_size = ceil(floor(limit / 4) / 3)
                cmd += f"adaptative avpkt {avpkt} bandwidth {bw}{bw_unit} burst {ceil(min_size / avpkt)} limit {limit}"
            else:
                cmd += f"perturb {perturb}"

        info(f'*** {self.__CLIENT} : ("{cmd}")\n')
        check_call(cmd, shell=True)

    def __create_output_dir(self) -> None:
        """Create the output directories."""
        info("*** Creating the output directories if they do not exist\n")
        sections = [host.name for host in self.__mn.net.hosts]
        sections.extend([f"s1-eth{i + 2}" for i in range(int(self.__n_hosts / 2))])

        for section in sections:
            output_dir = os.path.join(
                OUTPUT_BASE_DIR, self.__group, self.__name, section
            )

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

    def __format_output(self) -> None:
        """Format the Wireshark (TShark) output files."""
        info("*** Formatting the Wireshark (TShark) output files\n")

        for i in range(int(self.__n_hosts / 2)):
            s_eth = f"s1-eth{i + 2}"
            cmds = (
                [
                    f"tshark -r {os.path.join(OUTPUT_BASE_DIR, self.__group, self.__name, s_eth, self.__CAPTURE_FILE)} > {os.path.join(OUTPUT_BASE_DIR, self.__group, self.__name, s_eth, self.__OUTPUT_FILE)}"
                ]
                if self.__has_capture
                else []
            )
            cmds.append(
                f"tail -1 {os.path.join(OUTPUT_BASE_DIR, self.__group, self.__name, s_eth, self.__OUTPUT_FILE)}"
                + " | awk '{print $2}' > "
                + os.path.join(
                    OUTPUT_BASE_DIR,
                    self.__group,
                    self.__name,
                    s_eth,
                    self.__OUTPUT_FILE_FORMATTED,
                )
            )  # TODO: sometimes read nothing when no capture files.

            for cmd in cmds:
                info(f'*** {s_eth} : ("{cmd}")\n')
                check_call(cmd, shell=True)

    def __iperf_client(self, client_idx: int, n_b: int, n_b_unit_idx: int) -> None:
        """A multiprocessing task to run an iPerf client.

        Parameters
        ----------
        client_idx : int
            The index of the client host.
        n_b : int
            The number of bytes transferred from an iPerf client.
        n_b_unit_idx : int
            The index of the unit of the number of bytes transferred from an iPerf client.
        """
        cmd = f"iperf -c {self.__mn.net.hosts[client_idx + int(self.__n_hosts / 2)].IP()} -n {n_b}{self.__N_B_UNITS.get(n_b_unit_idx)} > " + os.path.join(
            OUTPUT_BASE_DIR,
            self.__group,
            self.__name,
            f"hl{client_idx + 1}",
            self.__OUTPUT_FILE,
        )
        info(f'*** hl{client_idx + 1} : ("{cmd}")\nIt starts at {datetime.now()}.\n')
        self.__mn.net.hosts[client_idx].cmd(cmd)

    def __launch_servers(self) -> None:
        """Launch iPerf in the server mode in the background."""
        info("*** Launching iPerf in the server mode in the background\n")

        for i in range(int(self.__n_hosts / 2), self.__n_hosts):
            self.__mn.net.hosts[i].cmdPrint(
                "iperf -i 1 -s > "
                + os.path.join(
                    OUTPUT_BASE_DIR,
                    self.__group,
                    self.__name,
                    f"hr{i - int(self.__n_hosts / 2) + 1}",
                    self.__OUTPUT_FILE,
                )
                + " &"
            )  # Add "&" in the end to run in the background.

    def __run_clients(self, n_b: int, n_b_unit: str) -> None:
        """Run iPerf clients almost simultaneously.

        Parameters
        ----------
        n_b : int
            The number of bytes transferred from an iPerf client.
        n_b_unit : str
            The unit of the number of bytes transferred from an iPerf client.
        """
        info("*** Running iPerf clients almost simultaneously\n")
        processes = []

        for i in range(int(self.__n_hosts / 2)):
            process = Process(
                target=self.__iperf_client,
                args=(
                    i,
                    n_b,
                    list(self.__N_B_UNITS.keys())[
                        list(self.__N_B_UNITS.values()).index(n_b_unit)
                    ],
                ),
            )
            processes.append(process)
            process.start()

        for process in processes:
            process.join()

    def __run_wireshark(self) -> None:
        """Run Wireshark (TShark) in the background."""
        info("*** Running Wireshark (TShark) in the background\n")
        processes = []

        for i in range(int(self.__n_hosts / 2)):
            process = Process(target=self.__wireshark, args=(i + 2,))
            processes.append(process)
            process.start()

        for process in processes:
            process.join()

        sleep(1)  # Wait for 1 second to ensure full capture.

    def __set_delay(self, delay: int) -> None:
        """Emulate high-latency WAN.

        Parameters
        ----------
        delay : int
            The latency in milliseconds.

        Raises
        ------
        BadCmdError
            The executed command fails, so the delay cannot be set. Check the command.
        """
        info("*** Emulating high-latency WAN\n")
        cmd = f"tc qdisc add dev s2-eth1 root netem delay {delay}ms"
        info(f'*** {self.__CLIENT} : ("{cmd}")\n')
        check_call(cmd, shell=True)

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

    def __summarise(self, n_b: int, n_b_unit: str, name: str) -> None:
        """Summarise the throughput and the flow completion time (FCT) for each relevant switch's interface in the summary file.

        Parameters
        ----------
        n_b : int
            The number of bytes transferred from an iPerf client.
        n_b_unit : str
            The unit of the number of bytes transferred from an iPerf client.
        name : str
            The experiment name.
        """
        info(
            "*** Summarising the throughput and the FCT for each relevant switch's interface in the summary file\n"
        )
        summary = name

        for i in range(int(self.__n_hosts / 2)):
            with open(
                os.path.join(
                    OUTPUT_BASE_DIR,
                    self.__group,
                    self.__name,
                    f"s1-eth{i + 2}",
                    self.__OUTPUT_FILE_FORMATTED,
                )
            ) as f:
                fct = f.readline().strip()

            if n_b_unit == "G":
                volume = n_b * 8 * 1024  # GB => Mbit
            elif n_b_unit == "K":
                volume = n_b * 8 / 1024  # KB => Mbit
            else:
                volume = n_b * 8  # MB => Mbit

            summary += f" {fct} {str(round(volume / float(fct)))}"  # TODO: throughput may be useless for fairness.

        with open(os.path.join(OUTPUT_BASE_DIR, self.__group, SUMMARY_FILE), "a") as f:
            f.write(summary + "\n")

    def __wireshark(self, s_eth_idx: int) -> None:
        """A multiprocessing task to run Wireshark (TShark).

        Parameters
        ----------
        s_eth_idx : int
            The index of a switch's interface for TCP traffic capture.
        """
        s_eth = f"s1-eth{s_eth_idx}"
        cmd = f"tshark -f 'tcp' -i {s_eth} " + (
            f"-w {os.path.join(OUTPUT_BASE_DIR, self.__group, self.__name, s_eth, self.__CAPTURE_FILE)} &"
            if self.__has_capture
            else f"> {os.path.join(OUTPUT_BASE_DIR, self.__group, self.__name, s_eth, self.__OUTPUT_FILE)} &"
        )
        info(f'*** {s_eth} : ("{cmd}")\nIt starts at {datetime.now()}.\n')
        check_call(cmd, shell=True, stderr=STDOUT, stdout=DEVNULL)

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
        group: str,
        name: str,
        alpha: int = ALPHA_DEFAULT,
        avpkt: int = 1000,
        aqm: str = None,
        beta: int = BETA_DEFAULT,
        bw: int = 1,
        bw_unit: str = "gbit",
        delay: int = 20,
        has_clean_lab: bool = False,
        interval: int = 100,
        limit: int = None,
        n: int = 2,
        n_b: int = 512,
        n_b_unit: str = N_B_UNIT_DEFAULT,
        perturb: int = 60,
        target: int = 5,
        tupdate: int = 15,
    ) -> None:
        """Do an experiment.

        Parameters
        ----------
        group : str
            The experiment group.
        name : str
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
        delay : int, optional
            The latency in milliseconds (the default is 20).
        has_clean_lab : bool, optional
            A flag indicating if the junk should be cleaned up to avoid any potential error before creating the simulation network (the default is `False`).
        interval : int, optional
            A value in milliseconds for CoDel to ensure that the measured minimum delay does not become too stale (the default is 100).
        limit : int, optional
            The default is `None`.
            For CoDel and PIE, the limit on the queue size in packets (the default is related to 10*BDP in the logic).
            For RED, the limit on the queue size in bytes (the default is 10*BDP in the logic).
            For TBF, the number of bytes that can be queued waiting for tokens to become available (the default is 10*BDP in the logic).
        n : int, optional
            The number of the hosts on each side of the dumbbell topology (the default is 2).
        n_b : int, optional
            The number of bytes transferred from an iPerf client (the default is 1).
        n_b_unit : str, optional
            The unit of the number of bytes transferred from an iPerf client (the default is defined by a constant "N_B_UNIT_DEFAULT", and the value should be one of the uppercases "G", "K", and "M").
        perturb : int, optional
            The interval in seconds for the queue algorithm perturbation in SFQ (the default is 60).
        target : int, optional
            For CoDel, the acceptable minimum standing/persistent queue delay in milliseconds (the default is 5).
            For PIE, the expected queue delay in milliseconds (the default is not for this case).
        tupdate : int, optional
            The frequency in milliseconds for PIE at which the system drop probability is calculated (the default is 15).

        Raises
        ------
        PoorPrepError
            BDP is not set. Check the call to the function `set_bdp()` before this function.
        """
        bw_unit = check_bw_unit(bw_unit=bw_unit)
        n_b_unit = n_b_unit.strip()

        if self.__bdp is None:
            raise PoorPrepError(message="BDP not set")

        if alpha >= beta or alpha < 0 or alpha > 32 or beta < 0 or beta > 32:
            alpha = ALPHA_DEFAULT
            beta = BETA_DEFAULT
            warning(
                "Invalid alpha and beta for PIE. The experiment defaults are used instead.\n"
            )

        if n_b_unit not in self.__N_B_UNITS.values():
            n_b_unit = N_B_UNIT_DEFAULT
            warning(
                "Invalid unit of the number of bytes transferred from an iPerf client. The experiment default is used instead.\n"
            )

        info(f"*** Starting the experiment: {group} - {name}\n")
        self.__group = group
        self.__mn.start(has_clean_lab=has_clean_lab, n=n)
        self.__n_hosts = len(self.__mn.net.hosts)
        self.__set_host_buffer()
        self.__apply_qdisc(
            alpha=alpha,
            avpkt=avpkt,
            beta=beta,
            bw=bw,
            bw_unit=bw_unit,
            interval=interval,
            limit=10 * self.__bdp if limit is None else limit,
            perturb=perturb,
            target=target,
            tupdate=tupdate,
        )  # Apply TBF.
        self.__set_delay(delay=delay)
        self.__name = name

        if aqm is not None:
            aqm = aqm.lower().strip()

            if aqm != "tbf":
                if limit is None:
                    if aqm == "red":
                        limit = 10 * self.__bdp
                    else:
                        limit = round(
                            10 * self.__bdp / 1500
                        )  # A TCP packet holds 1500 bytes of data at most.

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
                self.__name = aqm

        self.__create_output_dir()
        self.__run_wireshark()
        self.__launch_servers()
        self.__run_clients(n_b=n_b, n_b_unit=n_b_unit)
        quietRun(
            "killall -15 tshark"
        )  # Softly terminate any TShark that might still be running. Put the code here to reduce useless capture.
        quietRun(
            "killall -9 iperf"
        )  # Immediately terminate any iPerf that might still be running.
        self.__format_output()
        self.__summarise(n_b=n_b, n_b_unit=n_b_unit, name=name)
        self.__mn.stop()
        info("\n")

    def set_bdp(self, bw: int = 1, bw_unit: str = "gbit", delay: int = 20) -> None:
        """Set the bandwidth-delay product (BDP).

        Parameters
        ----------
        bw : int, optional
            The bandwidth for determining BDP (the default is 1).
        bw_unit : str, optional
            The bandwidth unit (the default is "gbit", and "mbit" is another accepted value).
        delay : int, optional
            The latency in milliseconds (the default is 20).

        Raises
        ------
        ValueError
            The bandwidth unit is invalid. Check if the value is one of "gbit" and "mbit".
        """
        bw_unit = check_bw_unit(bw_unit=bw_unit)
        self.__bdp = (
            bw * (1000000000 if bw_unit == "gbit" else 1000000) * delay / 1000 / 8
        )  # BDP (byte) = BW (bit/second) × RTT (second) / 8

        # Make BDP divisible by 1024.
        if self.__bdp % 1024 != 0:
            self.__bdp = ceil(self.__bdp / 1024) * 1024

        # BDP would not be smaller than the default buffer allocated when applications create a TCP socket.
        if self.__bdp < 87380:
            self.__bdp = 87380
