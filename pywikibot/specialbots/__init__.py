"""Module containing special bots reusable by scripts."""
#
# (C) Pywikibot team, 2020-2022
#
# Distributed under the terms of the MIT license.
#
from pywikibot.specialbots._unlink import BaseUnlinkBot, InteractiveUnlink
from pywikibot.specialbots._upload import UploadRobot


__all__ = (
    'BaseUnlinkBot',
    'InteractiveUnlink',
    'UploadRobot',
)
