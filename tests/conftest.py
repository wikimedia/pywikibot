# -*- coding: utf-8 -*-
"""Used by pytest to do some preparation work before running tests."""
#
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import sys


def pytest_configure(config):
    """Set the sys._test_runner_pytest flag to True, if pytest is used to run tests."""
    sys._test_runner_pytest = True
