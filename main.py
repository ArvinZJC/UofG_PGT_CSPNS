"""
'''
Description: the entry to the experiments and evaluation
Version: 2.0.0.20211125
Author: Arvin Zhao
Date: 2021-11-18 15:41:51
Last Editors: Arvin Zhao
LastEditTime: 2021-11-25 16:21:11
'''
"""

from mininet.clean import cleanup
from mininet.log import info, setLogLevel

from experiment import (
    Experiment,
    GROUP_A,
    GROUP_B,
    OUTPUT_BASE_DIR,
    OUTPUT_FILE_FORMATTED,
)
from eval import Eval

setLogLevel("info")
cleanup()  # NOTE: This line should be commented out after dev.
experiment = Experiment()
experiment.clear_output()
experiment.set_bdp()

info("\n*** 1 flow, specified amount, 1Gbps, all\n\n")
experiment.do(group=GROUP_A, has_wireshark=True, n=1)
experiment.do(aqm="CoDel", group=GROUP_A, has_wireshark=True, n=1)
experiment.do(aqm="PIE", group=GROUP_A, has_wireshark=True, n=1, target=15)
experiment.do(aqm="RED", group=GROUP_A, has_wireshark=True, n=1)
experiment.do(aqm="SFQ", group=GROUP_A, has_wireshark=True, n=1)

info("\n*** 1 flow, specified time, 1Gbps/100Mbps/10Mbps, all\n\n")
for bw in [1000, 100, 10]:
    bw = 1 if bw == 1000 else bw
    bw_unit = "gbit" if bw == 1 else "mbit"
    experiment.do(bw=bw, bw_unit=bw_unit, group=GROUP_B, n=1)
    experiment.do(aqm="CoDel", bw=bw, bw_unit=bw_unit, group=GROUP_B, n=1)
    experiment.do(aqm="PIE", bw=bw, bw_unit=bw_unit, group=GROUP_B, n=1, target=15)
    experiment.do(aqm="RED", bw=bw, bw_unit=bw_unit, group=GROUP_B, n=1)
    experiment.do(aqm="SFQ", bw=bw, bw_unit=bw_unit, group=GROUP_B, n=1)

info("\n*** 2 flows, same time, 1Gbps, all\n\n")
experiment.do(group=GROUP_B)
experiment.do(aqm="CoDel", group=GROUP_B)
experiment.do(aqm="PIE", group=GROUP_B, target=15)
experiment.do(aqm="RED", group=GROUP_B)
experiment.do(aqm="SFQ", group=GROUP_B)

info("\n*** Starting evaluation\n\n")
eval = Eval(base_dir=OUTPUT_BASE_DIR, file_formatted=OUTPUT_FILE_FORMATTED)
eval.plot_cwnd()
eval.plot_rtt()
eval.plot_throughput()
eval.plot_utilisation()
