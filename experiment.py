"""
'''
Description: the utilities of the experiments
Version: 2.0.0.20211201
Author: Arvin Zhao
Date: 2021-11-18 12:03:55
Last Editors: Arvin Zhao
LastEditTime: 2021-12-01 12:00:33
'''
"""

from datetime import datetime
from math import ceil, floor
from multiprocessing import Process
from shutil import rmtree
from subprocess import check_call, DEVNULL, PIPE, Popen, STDOUT
from time import sleep
import json
import os

from mininet.log import error, info, warning
from mininet.util import quietRun

from errors import PoorPrepError
from net import check_bw_unit, Net

ALPHA_DEFAULT = 2
BETA_DEFAULT = 25
BW_DEFAULT = 1
BW_UNIT_DEFAULT = "gbit"
DELAY_DEFAULT = 20
GROUP_A = "s_amount"  # Group A: transfer the specified/same amount of data.
GROUP_B = "s_time"  # Group B: transfer data for the specified/same time length.
N_B_UNIT_DEFAULT = "M"
OUTPUT_BASE_DIR = "output"  # The name of the output base directory.
OUTPUT_FILE = "result.txt"  # The filename with the file extension of the output file.
OUTPUT_FILE_FORMATTED = "result_new.txt"  # The filename with the file extension of the formatted output file.
QDISC = [
    "tbf",
    "ared",
    "codel",
    "pie",
    "sfq",
]  # A list of the supported classlist queueing disciplines.


class Experiment:
    """The class for defining the utilities of the experiments."""

    def __init__(self) -> None:
        """The constructor of the class for defining the utilities of the experiment settings."""
        self.__CAPTURE_FILE = (
            "result.pcapng"  # The filename with the file extension of the capture file.
        )
        self.__CLIENT = "client"  # The displayed name of the client in the outputs.
        self.__N_B_UNITS = {
            0: "G",
            1: "K",
            2: "M",
        }  # The dictionary of the units of the number of bytes transferred from an iperf client.
        self.__OUTPUT_JFILE = "result.json"  # The filename with the file extension of the output json file.
        self.__bdp = None
        self.__group = None  # The experiment group.
        self.__has_capture = None  # A flag indicating if the PCAPNG file should be generated using TShark.
        self.__has_tshark = None  # A flag indicating if the experiment should use TShark to capture traffic.
        self.__mn = Net()
        self.__n = 0  # The number of the hosts on each side of the dumbbell topology.
        self.__output_base_dir = None  # The experiment-specific output base directory.

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

        Support Adaptive Random Early Detection (ARED), Controlled Delay (CoDel), Stochastic Fair Queueing (SFQ), Token Bucket Filter (TBF), and Proportional Integral Controller-Enhanced (PIE).

        Parameters
        ----------
        alpha : int
            A smaller parameter for PIE to control the drop probability.
        avpkt : int
            A parameter for ARED used with the burst to determine the time constant for average queue size calculations.
        beta : int
            A larger parameter for PIE to control the drop probability.
        bw : int
            The bandwidth.
        bw_unit : str
            The bandwidth unit.
        interval : int
            A value in milliseconds for CoDel to ensure that the measured minimum delay does not become too stale.
        limit : int
            For ARED, the limit on the queue size in bytes.
            For CoDel and PIE, the limit on the queue size in packets.
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
        if qdisc not in QDISC:
            raise ValueError("invalid classless queueing discipline")

        info(f"*** Applying {qdisc.upper()}\n")
        cmd = "tc qdisc add dev s3-eth2 "

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
            cmd += f"parent 1: handle 2: {'red' if qdisc == 'ared' else qdisc} "

            if qdisc == "ared":
                # References:
                # 1. https://man7.org/linux/man-pages/man8/tc-red.8.html
                # 2. http://www.fifi.org/doc/HOWTO/en-html/Adv-Routing-HOWTO-14.html - Section 14.5
                min_size = ceil(floor(limit / 4) / 3)
                cmd += f"adaptative avpkt {avpkt} bandwidth {bw}{bw_unit} burst {ceil(min_size / avpkt)} ecn limit {limit}"
            elif qdisc == "codel":
                cmd += f"limit {limit} interval {interval}ms target {target}ms"
            elif qdisc == "pie":
                cmd += f"alpha {alpha} beta {beta} limit {limit} target {target}ms tupdate {tupdate}ms"
            else:
                cmd += f"perturb {perturb}"

        info(f'*** {self.__CLIENT} : ("{cmd}")\n')
        check_call(cmd, shell=True)

    def __client(self, client_idx: int, n_b: int, n_b_unit_idx: int, time: int) -> None:
        """A multiprocessing task to run an iperf3 client.

        Parameters
        ----------
        client_idx : int
            The index of the client host.
        n_b : int
            The number of bytes transferred from an iperf3 client.
        n_b_unit_idx : int
            The index of the unit of the number of bytes transferred from an iperf3 client.
        time : int
            The time in seconds for running an iperf3 client.
        """
        cmd = (
            f"iperf3 -c {self.__mn.net.hosts[client_idx + self.__n].IP()} -J -"
            + (
                f"n {n_b}{self.__N_B_UNITS.get(n_b_unit_idx)}"
                if self.__group == GROUP_A
                else f"t {time}"
            )
            + " > "
            + os.path.join(
                self.__output_base_dir, f"hl{client_idx + 1}", self.__OUTPUT_JFILE
            )
        )
        info(
            f'*** hl{client_idx + 1} : ("{cmd}")\nIt starts at {datetime.now()}'
            + (
                ""
                if self.__group == GROUP_A
                else f" and should last for {time} second(s)"
            )
            + ".\n"
        )
        self.__mn.net.hosts[client_idx].cmd(cmd)

    def __create_output_dir(self) -> None:
        """Create the output directories."""
        info("*** Creating the output directories if they do not exist\n")
        sections = [host.name for host in self.__mn.net.hosts]

        if self.__has_tshark:
            sections.extend([f"s1-eth{i + 2}" for i in range(self.__n)])

        for section in sections:
            output_dir = os.path.join(self.__output_base_dir, section)

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

    def __differentiate(self) -> None:
        """Differentiate flows to simulate different dynamic sharing the same bottleneck link."""
        info("*** Differentiating flows\n")

        for i in range(self.__n):
            if (i + 1) % 2 == 0:
                self.__mn.net.hosts[i].cmdPrint(
                    "sysctl -w net.ipv4.tcp_congestion_control=bbr"
                )

    def __format_output(self) -> None:
        """Format the output files."""
        info("*** Formatting the output files\n")

        for i in range(self.__n):
            output_formatted = os.path.join(
                self.__output_base_dir, f"hl{i + 1}", OUTPUT_FILE_FORMATTED
            )
            open(output_formatted, "w").write("")
            data = json.loads(
                open(
                    os.path.join(
                        self.__output_base_dir, f"hl{i + 1}", self.__OUTPUT_JFILE
                    ),
                    "r",
                ).read()
            )
            summary = (data.get("end").get("streams")[0]).get("sender")
            intervals = [
                interval.get("streams")[0] for interval in data.get("intervals")
            ]

            for interval in intervals:
                open(output_formatted, "a").write(
                    f"{interval.get('end')} {interval.get('bits_per_second') / 1000000} {interval.get('snd_cwnd') / 1000000} {interval.get('rtt') / 1000}\n"
                )  # end time (sec), throughput (Mbps), CWND (MB), RTT (ms)

            open(output_formatted, "a").write(
                f"{summary.get('end')} {summary.get('bits_per_second') / 1000000} {summary.get('max_snd_cwnd') / 1000000} {summary.get('mean_rtt') / 1000}\n"
            )  # FCT (sec), mean throughput (Mbps), max CWND (MB), mean RTT (ms)

    def __run_clients(self, n_b: int, n_b_unit: str, time: int) -> None:
        """Run the iperf3 client(s) almost simultaneously if applicable.

        Parameters
        ----------
        n_b : int
            The number of bytes transferred from an iperf3 client.
        n_b_unit : str
            The unit of the number of bytes transferred from an iperf3 client.
        time : int
            The time in seconds for running an iperf3 client.
        """
        info(
            "*** Running the iperf3 client"
            + ("s almost simultaneously" if self.__n > 1 else "")
            + "\n"
        )
        processes = []

        for i in range(self.__n):
            process = Process(
                target=self.__client,
                args=(
                    i,
                    n_b,
                    list(self.__N_B_UNITS.keys())[
                        list(self.__N_B_UNITS.values()).index(n_b_unit)
                    ],
                    time,
                ),
            )
            processes.append(process)
            process.start()

        for process in processes:
            process.join()

    def __run_servers(self) -> None:
        """Run iperf3 in the server mode in the background."""
        info("*** Running iperf3 in the server mode in the background\n")

        for i in range(self.__n, self.__n * 2):
            self.__mn.net.hosts[i].cmdPrint(
                "iperf3 -i 0 -s > "
                + os.path.join(
                    self.__output_base_dir, f"hr{i - self.__n + 1}", OUTPUT_FILE
                )
                + " &"
            )  # Add "&" in the end to run in the background.

    def __run_tshark(self) -> None:
        """Run TShark in the background."""
        info("*** Running TShark in the background\n")
        processes = []

        for i in range(self.__n):
            process = Process(target=self.__tshark, args=(i + 2,))
            processes.append(process)
            process.start()

        for process in processes:
            process.join()

        sleep(1)  # Wait for 1 second to ensure full capture.

    def __simulate(self, delay: int) -> None:
        """Simulate network latency and packet loss.

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
        cmd = f"tc qdisc add dev s2-eth2 root netem delay {delay}ms"
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

    def __tshark(self, s_eth_idx: int) -> None:
        """A multiprocessing task to run TShark.

        Parameters
        ----------
        s_eth_idx : int
            The index of a switch's interface for TCP traffic capture.
        """
        s_eth = f"s1-eth{s_eth_idx}"
        cmd = (
            f"tshark -f 'tcp' -i {s_eth} "
            + (
                f"-w {os.path.join(self.__output_base_dir, s_eth, self.__CAPTURE_FILE)}"
                if self.__has_capture
                else f"> {os.path.join(self.__output_base_dir, s_eth, OUTPUT_FILE)}"
            )
            + " &"
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
        alpha: int = ALPHA_DEFAULT,
        avpkt: int = 1000,
        aqm: str = "",
        beta: int = BETA_DEFAULT,
        bw: int = BW_DEFAULT,
        bw_unit: str = BW_UNIT_DEFAULT,
        delay: int = DELAY_DEFAULT,
        group_suffix: str = "",
        has_capture: bool = False,
        has_clean_lab: bool = False,
        has_tshark: bool = False,
        interval: int = 100,
        limit: int = 0,
        n: int = 2,
        n_b: int = 500,
        n_b_unit: str = N_B_UNIT_DEFAULT,
        perturb: int = 60,
        target: int = 5,
        time: int = 30,
        tupdate: int = 15,
    ) -> None:
        """Do an experiment.

        Parameters
        ----------
        group : str
            The experiment group (the value should be one of the values defined by the constants `GROUP_A` and `GROUP_B`).
        alpha : int, optional
            A smaller parameter for PIE to control the drop probability (the default is defined by a constant `ALPHA_DEFAULT`, and the value should be in the range between 0 and 32).
        aqm : str, optional
            A classless queueing discipline representing an AQM algorithm (the default is an empty string).
        avpkt : int, optional
            A parameter for ARED used with the burst to determine the time constant for average queue size calculations (the default is 1000).
        beta : int, optional
            A larger parameter for PIE to control the drop probability (the default is defined by a constant `BETA_DEFAULT`, and the value should be in the range between 0 and 32).
        bw : int, optional
            The bandwidth (the default is defined by a constant `BW_DEFAULT`).
        bw_unit : str, optional
            The bandwidth unit (the default is defined by a constant `BW_UNIT_DEFAULT`, and the value should be one of "gbit" and "mbit").
        delay : int, optional
            The latency in milliseconds (the default is defined by a constant `DELAY_DEFAULT`).
        group_suffix: str, optional
            The suffix added to the experiment group for the output directory (the default is an empty string).
        has_capture : bool, optional
            A flag indicating if the PCAPNG file should be generated using TShark (the default is `False`, and the disk space should be sufficient if the parameter is set to `True`).
        has_clean_lab : bool, optional
            A flag indicating if the junk should be cleaned up to avoid any potential error before creating the simulation network (the default is `False`).
        has_tshark : bool, optional
            A flag indicating if the experiment should use TShark to capture traffic (the default is `False`).
        interval : int, optional
            A value in milliseconds for CoDel to ensure that the measured minimum delay does not become too stale (the default is 100).
        limit : int, optional
            The number of bytes that can be queued waiting for tokens to become available (the default is 0, which means that it will be determined accordingly by the program).
            This parameter is directly used for ARED and TBF. CoDel and PIE require the limit on the queue size in packets. Hence, the value will be converted automatically to suit their needs.
        n : int, optional
            The number of the hosts on each side of the dumbbell topology (the default is 2, and the value should be in the range between 1 and 5).
        n_b : int, optional
            The number of bytes transferred from an iperf client (the default is 500).
        n_b_unit : str, optional
            The unit of the number of bytes transferred from an iperf client (the default is defined by a constant `N_B_UNIT_DEFAULT`, and the value should be one of the uppercases "G", "K", and "M").
        perturb : int, optional
            The interval in seconds for the queue algorithm perturbation in SFQ (the default is 60).
        target : int, optional
            For CoDel, the acceptable minimum standing/persistent queue delay in milliseconds (the default is 5).
            For PIE, the expected queue delay in milliseconds (the default is not for this case).
        time : int, optional
            The time in seconds for running an iperf client (the default is 30).
        tupdate : int, optional
            The frequency in milliseconds for PIE at which the system drop probability is calculated (the default is 15).

        Raises
        ------
        PoorPrepError
            BDP is not set. Check the call to the function `set_bdp()` before this function.
        ValueError
            The experiment group is invalid. Check if it is one of the specified values.
            The number of the hosts on each side of the dumbbell topology is invalid. Check if it is in the range between 1 and 5.
        """
        if self.__bdp is None:
            raise PoorPrepError(message="BDP not set")

        group = group.strip()

        if group not in [GROUP_A, GROUP_B]:
            raise ValueError("invalid experiment group")

        if n < 1 or n > 5:
            raise ValueError(
                "invalid number of the hosts on each side of the dumbbell topology"
            )

        bw_unit = check_bw_unit(bw_unit=bw_unit)
        aqm = aqm.strip().lower()
        limit = 10 * self.__bdp if limit == 0 else limit
        n_b_unit = n_b_unit.strip()
        name = "baseline" if aqm == "" or aqm == "tbf" else aqm  # The experiment name.
        self.__group = group
        self.__has_capture = has_capture
        self.__has_tshark = has_tshark
        self.__n = n
        self.__output_base_dir = os.path.join(
            OUTPUT_BASE_DIR,
            f"{self.__n}f",
            f"{self.__group}{group_suffix}",
            f"{bw}{bw_unit}",
            name,
        )

        info(f"*** Starting the experiment: {bw}{bw_unit} - {name}\n")
        self.__mn.start(has_clean_lab=has_clean_lab, n=self.__n)

        if self.__n > 1:
            self.__differentiate()

        self.__set_host_buffer()
        self.__simulate(delay=delay)
        self.__apply_qdisc(
            alpha=alpha,
            avpkt=avpkt,
            beta=beta,
            bw=bw,
            bw_unit=bw_unit,
            interval=interval,
            limit=limit,
            perturb=perturb,
            target=target,
            tupdate=tupdate,
        )  # Apply TBF.

        if aqm != "" and aqm != "tbf":
            if alpha >= beta or alpha < 0 or alpha > 32 or beta < 0 or beta > 32:
                alpha = ALPHA_DEFAULT
                beta = BETA_DEFAULT
                warning(
                    "Invalid alpha and beta for PIE. The experiment defaults are used instead.\n"
                )

            if aqm != "ared":
                limit = round(
                    limit / 1500
                )  # A TCP packet holds 1500 bytes of data at most.

            if n_b_unit not in self.__N_B_UNITS.values():
                n_b_unit = N_B_UNIT_DEFAULT
                warning(
                    "Invalid unit of the number of bytes transferred from an iperf client. The experiment default is used instead.\n"
                )

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

        self.__create_output_dir()

        if self.__has_tshark:
            self.__run_tshark()

        self.__run_servers()
        self.__run_clients(n_b=n_b, n_b_unit=n_b_unit, time=time)

        if self.__has_tshark:
            quietRun(
                f"killall -15 tshark"
            )  # Softly terminate any TShark that might still be running. Put the code here to reduce useless capture.

        quietRun(
            "killall -15 iperf3"
        )  # Softly terminate any iperf3 that might still be running.
        self.__format_output()
        self.__mn.stop()
        info("\n")

    def set_bdp(
        self,
        bw: int = BW_DEFAULT,
        bw_unit: str = BW_UNIT_DEFAULT,
        delay: int = DELAY_DEFAULT,
    ) -> None:
        """Set the bandwidth-delay product (BDP).

        Parameters
        ----------
        bw : int, optional
            The bandwidth for determining BDP (the default is defined by a constant `BW_DEFAULT`).
        bw_unit : str, optional
            The bandwidth unit (the default is defined by a constant `BW_UNIT_DEFAULT`, and the value should be one of "gbit" and "mbit").
        delay : int, optional
            The latency in milliseconds (the default is defined by a constant `DELAY_DEFAULT`).

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


# Simple test purposes only.
if __name__ == "__main__":
    from mininet.clean import cleanup
    from mininet.log import setLogLevel

    setLogLevel("info")
    cleanup()
    experiment = Experiment()
    experiment.clear_output()
    experiment.set_bdp()
    experiment.do(
        group=GROUP_A, group_suffix="_sp", has_tshark=True, limit=150000, n=1
    )  # limit = 100 * MTU
