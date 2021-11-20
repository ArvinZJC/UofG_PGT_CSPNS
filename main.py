"""
'''
Description: the entry to the experiments
Version: 2.0.0.20211120
Author: Arvin Zhao
Date: 2021-11-18 15:41:51
Last Editors: Arvin Zhao
LastEditTime: 2021-11-20 16:52:48
'''
"""

from mininet.log import setLogLevel

from experiment import Experiment, GROUP_A, GROUP_B

setLogLevel("info")
experiment = Experiment()
experiment.clear_output()
experiment.set_bdp()

for group in [GROUP_A, GROUP_B]:
    experiment.do(group=group, has_clean_lab=True)
    experiment.do(aqm="CoDel", group=group)
    experiment.do(aqm="PIE", group=group, target=15)
    experiment.do(aqm="RED", group=group)
    experiment.do(aqm="SFQ", group=group)
