"""
'''
Description: the utilities of the simulation dumbbell network for experiments
Version: 2.0.0.20211118
Author: Arvin Zhao
Date: 2021-11-18 14:54:13
Last Editors: Arvin Zhao
LastEditTime: 2021-11-18 16:35:16
'''
"""

from mininet.clean import cleanup
from mininet.link import TCLink
from mininet.log import info
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.util import dumpNodeConnections

from errors import PoorPrepError


class DumbbellTopo(Topo):
    """The class for defining a dumbbell topology."""

    def build(self, bw: int, bw_unit: str, delay: int, n: int) -> None:
        """Build up a dumbbell topology.

        Parameters
        ----------
        bw : int
            The bandwidth of the bottleneck.
        bw_unit : str
            The bandwidth unit.
        delay : int
            The latency of the bottleneck link in milliseconds.
        n : int
            The number of the hosts on each side of the dumbbell topology.
        """
        if check_bw_unit(bw_unit=bw_unit) == "gbit":
            bw *= 1000

        # Add 2 switches: the left for the sources and the right for the destinations.
        s1 = self.addSwitch(name="s1")
        s2 = self.addSwitch(name="s2")
        self.addLink(s1, s2, cls=TCLink, bw=bw, delay=f"{delay}ms")

        # Add the hosts on each side.
        for i in range(n):
            hl = self.addHost(name=f"hl{i + 1}")  # The left host (the source).
            hr = self.addHost(name=f"hr{i + 1}")  # The right host (the destination).
            self.addLink(hl, s1)
            self.addLink(hr, s2)


class Net:
    """The class for defining the utilities of the simulation dumbbell network for experiments."""

    def __init__(self) -> None:
        """The constructor of the class for defining the utilities of the simulation dumbbell network for experiments."""
        self.net = None  # Type: Mininet

    def start(
        self,
        bw: int = 1,
        bw_unit: str = "gbit",
        delay: int = 20,
        has_clean_lab: bool = False,
        n: int = 2,
    ) -> None:
        """Start the simulation dumbbell network and test its connectivity.

        Parameters
        ----------
        delay : int, optional
            The latency of the bottleneck link in milliseconds (the default is 20).
        has_clean_lab : bool, optional
            A flag indicating if the junk should be cleaned up to avoid any potential error before creating the simulation dumbbell network (the default is `False`).
        n : int, optional
            The number of hosts on each side of the dumbbell topology (the default is 2).
        """
        if has_clean_lab:
            cleanup()

        self.net = Mininet(
            topo=DumbbellTopo(
                bw=bw, bw_unit=check_bw_unit(bw_unit=bw_unit), delay=delay, n=n
            )
        )
        self.net.start()
        info("*** Dumping connections\n")
        dumpNodeConnections(self.net.switches)
        info("*** Testing network connectivity\n")
        self.net.pingAll()

    def stop(self, has_clean_lab: bool = True) -> None:
        """Stop the simulation dumbbell network and do cleanup if required.

        Parameters
        ----------
        has_clean_lab : bool, optional
            A flag indicating if the junk should be cleaned up after stopping the simulation dumbbell network (the default is `True`).

        Raises
        ------
        PoorPrepError
            No simulation dumbbell network is established. Check the call to the function `start()`.
        """
        if self.net is None:
            raise PoorPrepError(message="simulation dumbbell network undefined")

        self.net.stop()
        self.net = None

        if has_clean_lab:
            cleanup()


def check_bw_unit(bw_unit: str) -> str:
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


# Simple test purposes only.
if __name__ == "__main__":
    from mininet.log import error, setLogLevel

    setLogLevel("info")
    mn = Net()

    try:
        mn.start()
    except:
        error(
            "Failed to start the network. Cleanup will be executed before starting the network again."
        )
        mn.start(has_clean_lab=True)

    mn.stop()
