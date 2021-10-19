"""
'''
Description: the entry to the experiments
Version: 1.0.0.20211019
Author: Arvin Zhao
Date: 2021-10-10 15:41:51
Last Editors: Arvin Zhao
LastEditTime: 2021-10-19 10:39:21
'''
"""

from mininet.log import setLogLevel

from experiment import Experiment

setLogLevel("info")
experiment = Experiment()
experiment.clear_output()
experiment.set_bdp()
experiment.do(has_clean_lab=True)  # TODO: change to default when finishing dev.

# h1: cat result | grep sec | tr - " " | awk '{print $4,$8}' > output/h1/result_new
#
# h2: cat result | grep sec | tr - " " | awk '{print $4,$8}' > output/h2/result_new
#
# client: gnuplot
# client: plot "output/h1/result_new" title "tcp flow" with linespoints
