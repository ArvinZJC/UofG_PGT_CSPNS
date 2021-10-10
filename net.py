"""
'''
Description: the simulated network for experiments
Version: 1.0.0.20211010
Author: Arvin Zhao
Date: 2021-10-10 14:54:13
Last Editors: Arvin Zhao
LastEditTime: 2021-10-10 18:33:45
'''
"""

from mininet.clean import cleanup
from mininet.log import output
from mininet.net import Mininet
from mininet.node import Host, OVSKernelSwitch
from mininet.topo import Topo
from mininet.util import dumpNodeConnections


class Topology(Topo):
    """The class for defining a topology."""

    def build(self) -> None:
        """Build up a topology."""
        hosts = [
            self.addHost(cls=Host, defaultRoute=None, name="h%s" % (i + 1))
            for i in range(4)
        ]
        switches = [
            self.addSwitch(
                cls=OVSKernelSwitch, failMode="standalone", name="s%s" % (i + 1)
            )
            for i in range(3)
        ]
        host_idx = 0  # the host index for the selection of the hosts.

        for switch_no in [1, 3]:  # s1/s3
            self.addLink(switches[switch_no - 1], switches[1])

            for i in range(2):  # Each of s1 and s3 has 2 hosts.
                self.addLink(switches[switch_no - 1], hosts[host_idx])
                host_idx += 1


class Net:
    """The class for defining the simulated network for experiments."""

    def __init__(self) -> None:
        """The constructor of the class for defining the simulated network for experiments."""
        self.net = None  # Type: Mininet

    def start(self, has_clean_lab: bool = True) -> None:
        """Start the simulated network and test its connectivity.

        Parameters
        ----------
        has_clean_lab : bool
            A flag indicating if the junk should be cleaned up to avoid any potential error before creating the simulated network.
        """
        if has_clean_lab:
            cleanup()

        self.net = Mininet(topo=Topology())
        self.net.start()
        output("*** Dumping host connections:\n")
        dumpNodeConnections(self.net.hosts)
        output("*** Testing network connectivity:\n")
        self.net.pingAll()

    def stop(self, has_clean_lab: bool = True) -> None:
        """Stop the simulated network and do cleanup if required.

        Parameters
        ----------
        has_clean_lab : bool
            A flag indicating if the junk should be cleaned up after stopping the simulated network.
        """
        if self.net is None:
            print()  # TODO: raise exception.

        self.net.stop()

        if has_clean_lab:
            cleanup()


# Simple test purposes only.
if __name__ == "__main__":
    from mininet.log import setLogLevel

    setLogLevel("info")
    net = Net()
    net.start()
    net.stop()
