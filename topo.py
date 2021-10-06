#!/usr/bin/env python

'''
Description: the simulated topology for Mininet
Version: 1.0.0.20211006
Author: Jichen Zhao
Date: 2021-10-06 15:38:12
Last Editors: Jichen Zhao
LastEditTime: 2021-10-06 17:44:40
'''

from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import Host, OVSKernelSwitch
from mininet.topo import Topo
from mininet.util import dumpNodeConnections


class Topology(Topo):
    '''
    The class for defining a topology for experiments.
    '''

    def build(self, h: int = 2) -> None:
        '''
        Build up a Mininet network.

        Parameters
        ----------
        `h`: the number of hosts 
        '''

        h1 = self.addHost(
            cls = Host,
            defaultRoute = None,
            name = 'h1'
        )
        h2 = self.addHost(
            cls = Host,
            defaultRoute = None,
            name = 'h2'
        )
        h3 = self.addHost(
            cls = Host,
            defaultRoute = None,
            name = 'h3'
        )
        h4 = self.addHost(
            cls = Host,
            defaultRoute = None,
            name = 'h4'
        )

        s1 = self.addSwitch(
            cls = OVSKernelSwitch,
            failMode = 'standalone',
            name = 's1'
        )
        s2 = self.addSwitch(
            cls = OVSKernelSwitch,
            failMode = 'standalone',
            name = 's2'
        )
        s3 = self.addSwitch(
            cls = OVSKernelSwitch,
            failMode = 'standalone',
            name = 's3'
        )

        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(s1, s2)
        self.addLink(s2, s3)
        self.addLink(s3, h3)
        self.addLink(s3, h4)


def test_topo():
    '''
    Test the topology.
    '''

    net = Mininet(topo = Topology())
    net.start()
    print('Dumping host connections')
    dumpNodeConnections(net.hosts)
    print('Testing network connectivity')
    net.pingAll()
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    test_topo()