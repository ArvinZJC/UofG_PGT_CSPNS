"""
'''
Description: the entry to the experiments
Version: 1.0.0.20211027
Author: Arvin Zhao
Date: 2021-10-10 15:41:51
Last Editors: Arvin Zhao
LastEditTime: 2021-10-27 15:30:38
'''
"""

from mininet.log import setLogLevel

from experiment import Experiment

setLogLevel("info")
experiment = Experiment()
experiment.clear_output()
experiment.set_bdp()
# experiment.do(has_clean_lab=True)
experiment.do(has_clean_lab=True, time=5)
