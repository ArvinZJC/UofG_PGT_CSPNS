"""
'''
Description: the entry to the experiments
Version: 2.0.0.20211119
Author: Arvin Zhao
Date: 2021-11-18 15:41:51
Last Editors: Arvin Zhao
LastEditTime: 2021-11-19 19:04:33
'''
"""

from mininet.log import setLogLevel

from experiment import Experiment

setLogLevel("info")
experiment = Experiment()
experiment.clear_output()
experiment.set_bdp()

# Fairness.
group = "fairness"
experiment.do(group=group, has_clean_lab=True, name="baseline")
experiment.do(aqm="CoDel", group=group, name="CoDel")
experiment.do(aqm="PIE", group=group, name="PIE", target=15)
experiment.do(aqm="RED", group=group, name="RED")
experiment.do(aqm="SFQ", group=group, name="SFQ")
