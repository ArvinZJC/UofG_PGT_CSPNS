"""
'''
Description: the entry to the experiments
Version: 1.0.0.20211028
Author: Arvin Zhao
Date: 2021-10-10 15:41:51
Last Editors: Arvin Zhao
LastEditTime: 2021-10-28 19:09:58
'''
"""

from mininet.log import setLogLevel

from experiment import Experiment

setLogLevel("info")
experiment = Experiment()
experiment.clear_output()
experiment.set_bdp()
experiment.do(has_clean_lab=True, time=5)
# experiment.do(aqm="CoDel", time=5)
# experiment.do(aqm="PIE", time=5)
# experiment.do(aqm="RED", time=5)
# experiment.do(aqm="SFQ", time=5)
