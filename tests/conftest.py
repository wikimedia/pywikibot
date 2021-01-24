"""Used by pytest to do some preparation work before running tests."""
#
# (C) Pywikibot team, 2016-2020
#
# Distributed under the terms of the MIT license.
#
import sys


def pytest_configure(config):
    """Set the sys._test_runner_pytest flag to True, if pytest is used."""
    sys._test_runner_pytest = True
