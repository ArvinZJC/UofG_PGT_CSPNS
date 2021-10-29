"""
'''
Description: the entry to the experiments
Version: 1.0.0.20211029
Author: Arvin Zhao
Date: 2021-10-10 15:41:51
Last Editors: Arvin Zhao
LastEditTime: 2021-10-29 15:38:35
'''
"""

from mininet.log import setLogLevel

from experiment import Experiment

setLogLevel("info")
experiment = Experiment()
experiment.clear_output()
experiment.set_bdp()
experiment.do(has_clean_lab=True, name="baseline", time=5)
experiment.do(aqm="CoDel", name="CoDel", time=5)
experiment.do(aqm="PIE", name="PIE", target=15, time=5)
experiment.do(aqm="RED", name="RED", time=5)
experiment.do(aqm="SFQ", name="SFQ", time=5)
