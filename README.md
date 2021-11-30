# UofG_PGT_CSPNS

![GitHub](https://img.shields.io/github/license/ArvinZJC/UofG_PGT_CSPNS)

This repository contains code written for doing a **CS Project for Networked Systems** during the PGT study of MSc Computing Science in UofG. Please note that the code is licensed under [the MIT License](./LICENSE).

## ATTENTION

1. By 30 November 2021, everything looks good with Ubuntu 20.04.3 LTS + Visual Studio Code (Version: 1.62.3) + Mininet 2.3.0 + Python 3.8.10. To reproduce experiment results, you need to ensure that the following tools can work properly. TShark should be installed with Mininet, and you may install iperf3 manually.

    | Name | Version |
    | :-- | :--: |
    | iperf3 | 3.7 |
    | TShark | 3.2.3 |

2. To execute the Python scripts, you need to install some packages listed as follows. Please refer to [the package requirements for this project](./requirements.txt).

    | Name | Version |
    | :-- | :--: |
    | matplotlib | 3.5.0 |
    | pandas | 1.3.4 |

3. The project relates to the evaluation of 4 different Active Queue Management (AQM) mechanisms over different network setups. For more info, please refer to the project report.
    - Adaptive Random Early Detection (ARED)
    - Controlled Delay (CoDel)
    - Proportional Integral Controller-Enhanced (PIE)
    - Stochastic Fairness Queuing (SFQ)
