"""
'''
Description: the entry to the experiments
Version: 1.0.0.20211018
Author: Arvin Zhao
Date: 2021-10-10 15:41:51
Last Editors: Arvin Zhao
LastEditTime: 2021-10-18 19:23:58
'''
"""

from mininet.log import setLogLevel

from experiment import Experiment

setLogLevel("info")
experiment = Experiment()
experiment.set_bdp()
experiment.do()

# from mininet.cli import CLI
# CLI(mininet=mn.net)
# cli: xterm h1 h2 h3 h4
#
# h3: iperf -i 1 -s > output/h3/result
#
# h4: iperf -i 1 -s > output/h4/result
#
# h1 (sync with h2): iperf -c 10.0.0.3 -i 1 -t 60 > output/h1/result
# h1: cat result | grep sec | tr - " " | awk '{print $4,$8}' > output/h1/result_new
#
# h2 (sync with h1): iperf -c 10.0.0.4 -i 1 -t 60 > output/h2/result
# h2: cat result | grep sec | tr - " " | awk '{print $4,$8}' > output/h2/result_new
#
# client: gnuplot
# client: plot "output/h1/result_new" title "tcp flow" with linespoints
