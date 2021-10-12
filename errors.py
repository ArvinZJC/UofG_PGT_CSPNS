"""
'''
Description: user-defined exceptions for the project
Version: 1.0.0.20211011
Author: Arvin Zhao
Date: 2021-10-11 16:57:58
Last Editors: Arvin Zhao
LastEditTime: 2021-10-11 20:28:46
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


class UndefinedNetError(Exception):
    """The class for defining the user-defined exception indicating that no simulated network is established."""

    def __init__(self, message: str = "simulated network undefined") -> None:
        """The constructor of the class for defining the user-defined exception indicating that no simulated network is established.

        Parameters
        ----------
        message : str, optional
            The error message (the default is "simulated network undefined").
        """
        super().__init__(message)
