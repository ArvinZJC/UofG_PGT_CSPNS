"""
Description: 
Version: 
Author: Arvin Zhao
Date: 2021-11-23 19:02:29
Last Editors: 
LastEditTime: 2021-11-23 19:02:29
"""
import re

matches = re.findall(
    re.compile(r"backlog\s[^\s]+\s([\d]+)p"),
    "qdisc tbf 1: root refcnt 2 rate 1Gbit burst 500000b lat 196.0ms \n Sent 836 bytes 10 pkt (dropped 0, overlimits 0 requeues 0) \n backlog 0b 12p requeues 0\n",
)
print(matches)
