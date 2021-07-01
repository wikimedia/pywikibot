#!/usr/bin/python
"""Module containing special bots reusable by scripts."""
#
# (C) Pywikibot team, 2020-2021
#
# Distributed under the terms of the MIT license.
#
from pywikibot.specialbots._unlink import BaseUnlinkBot, InteractiveUnlink
from pywikibot.specialbots._upload import UploadRobot
from pywikibot.tools import ModuleDeprecationWrapper, suppress_warnings


with suppress_warnings(category=FutureWarning):
    from pywikibot.specialbots._unlink import EditReplacement

__all__ = (
    'BaseUnlinkBot',
    'EditReplacement',
    'InteractiveUnlink',
    'UploadRobot',
)

wrapper = ModuleDeprecationWrapper(__name__)
wrapper.add_deprecated_attr(
    'EditReplacement',
    replacement_name='pywikibot.exceptions.EditReplacementError',
    since='20210423')
