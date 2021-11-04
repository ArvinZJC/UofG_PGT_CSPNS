"""
'''
Description: the entry to the experiments
Version: 1.0.0.20211104
Author: Arvin Zhao
Date: 2021-10-10 15:41:51
Last Editors: Arvin Zhao
LastEditTime: 2021-11-04 21:52:18
'''
"""

from mininet.log import setLogLevel

from experiment import Experiment
from eval import plot_fct, plot_throughput

setLogLevel("info")
experiment = Experiment()
experiment.clear_output()
experiment.set_bdp()
experiment.do(has_clean_lab=True, name="baseline")
experiment.do(aqm="CoDel", name="CoDel")
experiment.do(aqm="PIE", name="PIE", target=15)
experiment.do(aqm="RED", name="RED")
experiment.do(aqm="SFQ", name="SFQ")
plot_fct()
plot_throughput()
