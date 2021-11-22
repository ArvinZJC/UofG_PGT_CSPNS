"""
'''
Description: the entry to the experiments and evaluation
Version: 2.0.0.20211122
Author: Arvin Zhao
Date: 2021-11-18 15:41:51
Last Editors: Arvin Zhao
LastEditTime: 2021-11-22 22:40:10
'''
"""

from mininet.log import setLogLevel

from experiment import (
    Experiment,
    GROUP_A,
    GROUP_B,
    OUTPUT_BASE_DIR,
    OUTPUT_FILE_FORMATTED,
)
from eval import Eval

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

# Only execute the evaluation module if the output results are expected no changes.
eval = Eval(base_dir=OUTPUT_BASE_DIR, file_formatted=OUTPUT_FILE_FORMATTED)
eval.plot_throughput(group=GROUP_B)
eval.plot_utilisation(group=GROUP_B)
