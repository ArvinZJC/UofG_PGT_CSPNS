"""
'''
Description: the utilities of the simulated network for experiments
Version: 1.0.0.20211019
Author: Arvin Zhao
Date: 2021-10-10 14:54:13
Last Editors: Arvin Zhao
LastEditTime: 2021-10-19 01:46:10
'''
"""

from mininet.clean import cleanup
from mininet.log import info
from mininet.net import Mininet
from mininet.topolib import TreeTopo
from mininet.util import dumpNodeConnections

from errors import PoorPrepError


class Net:
    """The class for defining the utilities of the simulated network with Mininet for experiments."""

    def __init__(self) -> None:
        """The constructor of the class for defining the utilities of the simulated network with Mininet for experiments."""
        self.net = None  # Type: Mininet

    def start(self, has_clean_lab: bool = False) -> None:
        """Start the simulated network and test its connectivity.

        Parameters
        ----------
        has_clean_lab : bool, optional
            A flag indicating if the junk should be cleaned up to avoid any potential error before creating the simulated network (the default is `False`).
        """
        if has_clean_lab:
            cleanup()

        self.net = Mininet(
            topo=TreeTopo(depth=2, fanout=2)
        )  # Create a tree topology with 4 hosts and 3 switches (as the structure shown in topo.mn).
        self.net.start()
        info("*** Dumping host connections\n")
        dumpNodeConnections(self.net.hosts)
        info("*** Testing network connectivity\n")
        self.net.pingAll()

    def stop(self, has_clean_lab: bool = True) -> None:
        """Stop the simulated network and do cleanup if required.

        Parameters
        ----------
        has_clean_lab : bool, optional
            A flag indicating if the junk should be cleaned up after stopping the simulated network (the default is `True`).

        Raises
        ------
        PoorPrepError
            No simulated network is established. Check the call to the function `start()`.
        """
        if self.net is None:
            raise PoorPrepError(message="simulated network undefined")

        self.net.stop()
        self.net = None

        if has_clean_lab:
            cleanup()


# Simple test purposes only.
if __name__ == "__main__":
    from mininet.log import setLogLevel

    setLogLevel("info")
    mn = Net()
    mn.start()
    mn.stop()
