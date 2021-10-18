"""
'''
Description: user-defined exceptions for the project
Version: 1.0.0.20211018
Author: Arvin Zhao
Date: 2021-10-11 16:57:58
Last Editors: Arvin Zhao
LastEditTime: 2021-10-18 15:38:18
'''
"""


class BadCmdError(Exception):
    """The class for defining the user-defined exception indicating that the executed command fails."""

    def __init__(self, message: str = "bad command fails") -> None:
        """The constructor of the class for defining the user-defined exception indicating that the executed command fails.

        Parameters
        ----------
        message : str, optional
            The error message (the default is "bad command fails").
        """
        super.__init__(message)


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
