"""
'''
Description: the entry to the experiments
Version: 2.0.0.20211118
Author: Arvin Zhao
Date: 2021-11-18 15:41:51
Last Editors: Arvin Zhao
LastEditTime: 2021-11-18 22:41:00
'''
"""

from mininet.log import setLogLevel

from experiment import Experiment

setLogLevel("info")
experiment = Experiment(has_capture=True)
experiment.clear_output()
experiment.set_bdp()
experiment.do(has_clean_lab=True, name="baseline")
experiment.do(aqm="CoDel", name="CoDel")
experiment.do(aqm="PIE", name="PIE", target=15)
experiment.do(aqm="RED", name="RED")
experiment.do(aqm="SFQ", name="SFQ")
