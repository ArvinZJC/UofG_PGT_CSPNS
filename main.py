"""
'''
Description: the entry to the experiments
Version: 1.0.0.20211011
Author: Arvin Zhao
Date: 2021-10-10 15:41:51
Last Editors: Arvin Zhao
LastEditTime: 2021-10-11 22:12:19
'''
"""

import os

from mininet.cli import CLI
from mininet.log import info, setLogLevel

from errors import BadCmdError
from net import Net

setLogLevel("info")
mn = Net()
mn.start(has_clean_lab=True)  # TODO: change to default when finishing dev.

mn.net.hosts[0].cmdPrint("ping -c4", mn.net.hosts[2].IP())
cmd = "tc qdisc add dev s2-eth1 root netem delay 20ms"  # TODO: name for s2-eth1 (for h1-eth0)?
info('*** %s : ("%s")\n' % ("client", cmd))

if not os.WIFEXITED(os.system(cmd)):
    raise BadCmdError

mn.net.hosts[0].cmdPrint("ping -c4", mn.net.hosts[2].IP())

for host in mn.net.hosts:
    host.cmdPrint("sysctl -w net.ipv4.tcp_rmem='10240 87380 52428800'")
    host.cmdPrint("sysctl -w net.ipv4.tcp_wmem='10240 87380 52428800'")

mn.net.hosts[0].cmdPrint("sysctl net.ipv4.tcp_congestion_control")
mn.net.hosts[1].cmdPrint("sysctl -w net.ipv4.tcp_congestion_control=bbr")

cmd = "tc qdisc add dev s1-eth2 root handle 1: tbf rate 1gbit burst 500000 limit 26214400"  # TODO: name for s1-eth2 (for s3)?
info('*** %s : ("%s")\n' % ("client", cmd))

if not os.WIFEXITED(os.system(cmd)):
    raise BadCmdError

CLI(mininet=mn.net)
# cli: xterm h1 h2 h3 h4
#
# h3: mkdir output/h3 && cd output/h3
# h3: iperf -i 1 -s > result
#
# h4: mkdir output/h4 && cd output/h4
# h4: iperf -i 1 -s > result
#
# h1: mkdir output/h1 && cd output/h1
# h1 (sync with h2): iperf -c 10.0.0.3 -i 1 -t 60 > result
# h1: cat result | grep sec | tr - " " | awk '{print $4,$8}' > result_new
#
# h2: mkdir output/h2 && cd output/h2
# h2 (sync with h1): iperf -c 10.0.0.4 -i 1 -t 60 > result
# h2: cat result | grep sec | tr - " " | awk '{print $4,$8}' > result_new
#
# client: gnuplot
# client: plot "output/h1/result_new" title "tcp flow" with linespoints

mn.stop()
