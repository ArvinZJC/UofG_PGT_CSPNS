"""
'''
Description: the entry to the experiments
Version: 1.0.0.20211010
Author: Arvin Zhao
Date: 2021-10-10 15:41:51
Last Editors: Arvin Zhao
LastEditTime: 2021-10-10 21:07:14
'''
"""

import os

from mininet.log import setLogLevel

from net import Net

setLogLevel("info")
net = Net()
net.start()

# net.net.hosts[0].cmdPrint("ping -c4", net.net.hosts[2].IP())
# os.system("tc qdisc add dev s1-eth1 root netem delay 20ms")
# net.net.hosts[0].cmdPrint("ping -c4", net.net.hosts[2].IP())

for host in net.net.hosts:
    host.cmdPrint("sysctl -w net.ipv4.tcp_rmem='10240 87380 52428800")
    host.cmdPrint("sysctl -w net.ipv4.tcp_wmem='10240 87380 52428800")

net.net.hosts[0].cmdPrint("sysctl net.ipv4.tcp_congestion_control")
net.net.hosts[1].cmdPrint("sysctl -w net.ipv4.tcp_congestion_control=bbr")

os.system(
    "tc qdisc add dev s2-eth2 root handle 1: tbf rate 1gbit burst 500000 limit 26214400"
)

net.stop()
