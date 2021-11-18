"""
'''
Description: user-defined exceptions for the project
Version: 1.0.0.20211101
Author: Arvin Zhao
Date: 2021-10-11 16:57:58
Last Editors: Arvin Zhao
LastEditTime: 2021-11-01 16:36:54
'''
"""


class PoorPrepError(Exception):
    """The class for defining the user-defined exception indicating that the preparation for an experiment is insufficient."""

    def __init__(self, message: str = "poor preparation for an experiment") -> None:
        """The constructor of the class for defining the user-defined exception indicating that the preparation for an experiment is insufficient.

        Parameters
        ----------
        message : str, optional
            The error message (the default is "poor preparation for an experiment").
        """
        super().__init__(message)
