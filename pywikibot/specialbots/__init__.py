#!/usr/bin/python
"""Module containing special bots reusable by scripts."""
#
# (C) Pywikibot team, 2020-2021
#
# Distributed under the terms of the MIT license.
#
from pywikibot.specialbots._unlink import (
    EditReplacement, InteractiveUnlink, BaseUnlinkBot
)
from pywikibot.specialbots._upload import UploadRobot


__all__ = (
    'BaseUnlinkBot',
    'EditReplacement',
    'InteractiveUnlink',
    'UploadRobot',
)
