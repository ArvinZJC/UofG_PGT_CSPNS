"""
'''
Description: the utilities of the experiment settings
Version: 1.0.0.20211018
Author: Arvin Zhao
Date: 2021-10-18 12:03:55
Last Editors: Arvin Zhao
LastEditTime: 2021-10-18 19:29:04
'''
"""

from math import ceil
from subprocess import Popen, PIPE
import os
from time import sleep

from mininet.log import info

from errors import BadCmdError, PoorPrepError
from net import Net


class Experiment:
    """The class for defining the utilities of the experiment settings."""

    def __init__(self, rtt: int = 20) -> None:
        """The constructor of the class for defining the utilities of the experiment settings.
        
        Parameters
        ----------
        rtt : int
            The round-trip time (RTT) latency in millisecond (the default is 20).
        
        Raises
        ------
        ValueError
            The value for RTT is invalid. Set a value larger than 0 but no larger than 4294967.
        """
        self.__OUTPUT_BASE_DIR = "output"
        self.__bdp = None
        self.__mn = Net()

        # No longer than the max time value of the Linux command `tc`.
        if rtt <= 0 and rtt > 4294967:
            raise ValueError("invalid RTT value")

        self.__rtt = rtt

    def __apply_qdisc(self, bw: int, bw_unit: str, limit: int, qdisc: str = "tbf") -> None:
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
        qdisc : str
            A classless queueing discipline (the default is "tbf", and the other accepted values are TODO).
        
        Raises
        ------
        BadCmdError
            The executed command fails, so the classless queueing discipline is not applied. Check the command.
        """
        info(f"*** Applying {qdisc.upper()}\n")
        cmd = "tc qdisc add dev s1-eth2 "

        if qdisc == "tbf":
            hz = int(Popen("egrep '^CONFIG_HZ_[0-9]+' /boot/config-`uname -r`", shell=True, stdout=PIPE).stdout.read().decode().replace("CONFIG_HZ_", "").replace("=y\n", ""))
            burst = int(bw * (1000000000 if bw_unit == "gbit" else 1000000) / hz / 8)  # Reference: https://unix.stackexchange.com/a/100797
            cmd += f"root handle 1: {qdisc} burst {burst} limit {limit} rate {bw}{bw_unit}"
        else:
            cmd += f"parent 1: handle 2: {qdisc} "

            # TODO:

        info('*** %s : ("%s")\n' % ("client", cmd))

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
            output_dir = os.path.join(self.__OUTPUT_BASE_DIR, host.name)
                
            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

    def __set_delay(self) -> None:
        """Emulate high-latency WAN.
        
        Raises
        ------
        BadCmdError
            The executed command fails, so the delay cannot be set. Check the command.
        """
        info("*** Emulating high-latency WAN\n")
        self.__mn.net.hosts[0].cmdPrint("ping -c4", self.__mn.net.hosts[2].IP())
        cmd = f"tc qdisc add dev s2-eth1 root netem delay {self.__rtt}ms"  # Set the delay on s2-eth1 to affect h1 and h2.
        info('*** %s : ("%s")\n' % ("client", cmd))

        if not os.WIFEXITED(os.system(cmd)):
            raise BadCmdError

        self.__mn.net.hosts[0].cmdPrint("ping -c4", self.__mn.net.hosts[2].IP())

    def __set_host_buffer(self) -> None:
        """Set the hosts' buffer size."""
        info("*** Setting the hosts' buffer size\n")

        for host in self.__mn.net.hosts:
            host.cmdPrint(f"sysctl -w net.ipv4.tcp_rmem='10240 87380 {20 * self.__bdp}'")  # Buffer size: 'minimum default maximum (20·BDP)'.
            host.cmdPrint(f"sysctl -w net.ipv4.tcp_wmem='10240 87380 {20 * self.__bdp}'")

    def apply_aqm(self, aqm: str) -> None:
        """Apply an Active Queue Management (AQM) algorithm.

        Parameters
        ----------
        aqm : str
            A classless queueing discipline representing an AQM algorithm.
        
        Raises
        ------
        ValueError
            TODO The AQM algorithm is invalid. Check if the value is one of "codel".
        """
        aqm = aqm.lower().strip()

        if aqm not in ["codel"]:
            raise ValueError("invalid AQM algorithm")
        
        # TODO:

    def do(
        self,
        aqm: str = None,
        bw: int = 1,
        bw_unit: str = "gbit"
    ) -> None:
        """Do an experiment.
        
        Parameters
        ----------
        aqm : str
            A classless queueing discipline representing an AQM algorithm (the default is `None`).
        bw : int
            The bandwidth (the default is 1).
        bw_unit : str
            The bandwidth unit (the default is "gbit", and "mbit" is another accepted value).
        
        Raises
        ------
        PoorPrepError
            BDP is not set. Check the call to the function `set_bdp()` before this function.
        """
        bw_unit = self.__check_bw_unit(bw_unit=bw_unit)

        if self.__bdp is None:
            raise PoorPrepError(message="BDP not set")

        self.__mn.start(has_clean_lab=True)  # TODO: change to default when finishing dev.
        self.__set_delay()
        self.__set_host_buffer()
        self.__apply_qdisc(bw=bw, bw_unit=bw_unit, limit = 10 * self.__bdp)  # Apply TBF.
        # TODO: AQM
        self.__create_output_dir()
        self.__mn.net.hosts[2].sendCmd("iperf -i 1 -s > output/h3/result")
        sleep(1000)
        self.__mn.net.hosts[2].sendInt()
        self.__mn.stop()

    def set_bdp(self, bw: int = 1, bw_unit: str = "gbit") -> None:
        """Set the bandwidth-delay product (BDP).
        
        Parameters
        ----------
        bw : int
            The bandwidth for determining BDP (the default is 1).
        bw_unit : str
            The bandwidth unit (the default is "gbit", and "mbit" is another accepted value).
        
        Raises
        ------
        ValueError
            The bandwidth unit is invalid. Check if the value is one of "gbit" and "mbit".
        """
        bw_unit = self.__check_bw_unit(bw_unit=bw_unit)
        self.__bdp = bw * (1000000000 if bw_unit == "gbit" else 1000000) * self.__rtt / 1000 / 8  # BDP (byte) = BW (bit/second) × RTT (second) / 8

        # Make BDP divisible by 1024.
        if self.__bdp % 1024 != 0:
            self.__bdp = ceil(self.__bdp / 1024) * 1024
        
        # BDP would not be smaller than the default buffer allocated when applications create a TCP socket.
        if self.__bdp < 87380:
            self.__bdp = 87380
