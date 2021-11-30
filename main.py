"""
'''
Description: the entry to the experiments and evaluation
Version: 2.0.0.20211130
Author: Arvin Zhao
Date: 2021-11-18 15:41:51
Last Editors: Arvin Zhao
LastEditTime: 2021-11-30 15:21:27
'''
"""

from mininet.clean import cleanup
from mininet.log import info, setLogLevel

from experiment import (
    Experiment,
    GROUP_A,
    GROUP_B,
    OUTPUT_BASE_DIR,
    OUTPUT_FILE,
    OUTPUT_FILE_FORMATTED,
)
from eval import Eval

setLogLevel("info")
cleanup()  # NOTE: This line should be commented out after dev.
experiment = Experiment()
experiment.clear_output()
experiment.set_bdp()
bw_settings = [1000, 100, 10]

info("\n*** 1 flow, specified amount, 1 Gbps, all\n\n")
experiment.do(group=GROUP_A, n=1)
experiment.do(aqm="ARED", group=GROUP_A, n=1)
experiment.do(aqm="CoDel", group=GROUP_A, n=1)
experiment.do(aqm="PIE", group=GROUP_A, n=1, target=15)
experiment.do(aqm="SFQ", group=GROUP_A, n=1)

info("\n*** 1 flow, specified amount (limit changed for small buffer), 1 Gbps, all\n\n")
group_suffix = "_sp"
experiment.do(
    group=GROUP_A, group_suffix=group_suffix, has_tshark=True, limit=150000, n=1
)
experiment.do(
    aqm="ARED",
    group=GROUP_A,
    group_suffix=group_suffix,
    has_tshark=True,
    limit=150000,
    n=1,
)
experiment.do(
    aqm="CoDel",
    group=GROUP_A,
    group_suffix=group_suffix,
    has_tshark=True,
    limit=150000,
    n=1,
)
experiment.do(
    aqm="PIE",
    group=GROUP_A,
    group_suffix=group_suffix,
    has_tshark=True,
    limit=150000,
    n=1,
    target=15,
)
experiment.do(
    aqm="SFQ",
    group=GROUP_A,
    group_suffix=group_suffix,
    has_tshark=True,
    limit=150000,
    n=1,
)

info("\n*** 1 flow, specified time, 1 Gbps/100 Mbps/10 Mbps, all\n\n")
for bw in bw_settings:
    bw = 1 if bw == 1000 else bw
    bw_unit = "gbit" if bw == 1 else "mbit"
    experiment.do(bw=bw, bw_unit=bw_unit, group=GROUP_B, n=1)
    experiment.do(aqm="ARED", bw=bw, bw_unit=bw_unit, group=GROUP_B, n=1)
    experiment.do(aqm="CoDel", bw=bw, bw_unit=bw_unit, group=GROUP_B, n=1)
    experiment.do(aqm="PIE", bw=bw, bw_unit=bw_unit, group=GROUP_B, n=1, target=15)
    experiment.do(aqm="SFQ", bw=bw, bw_unit=bw_unit, group=GROUP_B, n=1)

info("\n*** 2 flows, same time, 1 Gbps/100 Mbps/10 Mbps, all\n\n")
for bw in bw_settings:
    bw = 1 if bw == 1000 else bw
    bw_unit = "gbit" if bw == 1 else "mbit"
    experiment.do(bw=bw, bw_unit=bw_unit, group=GROUP_B)
    experiment.do(aqm="ARED", bw=bw, bw_unit=bw_unit, group=GROUP_B)
    experiment.do(aqm="CoDel", bw=bw, bw_unit=bw_unit, group=GROUP_B)
    experiment.do(aqm="PIE", bw=bw, bw_unit=bw_unit, group=GROUP_B, target=15)
    experiment.do(aqm="SFQ", bw=bw, bw_unit=bw_unit, group=GROUP_B)

info("\n*** Starting evaluation\n\n")
eval = Eval(
    base_dir=OUTPUT_BASE_DIR, file=OUTPUT_FILE, file_formatted=OUTPUT_FILE_FORMATTED
)
eval.plot_cwnd()
eval.plot_fct()
eval.plot_fct(group_suffix=group_suffix)
eval.plot_rr(group_suffix=group_suffix)
eval.plot_rtt()
eval.plot_throughput()
eval.plot_utilisation()
