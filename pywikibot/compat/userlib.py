# -*- coding: utf-8  -*-
"""
WARNING: THIS MODULE EXISTS SOLELY TO PROVIDE BACKWARDS-COMPATIBILITY.

Do not use in new scripts; use the source to find the appropriate
function/method instead.

"""
#
# (C) Pywikibot team, 2008
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'


from pywikibot import User
from pywikibot.tools import ModuleDeprecationWrapper

__all__ = ('User',)

wrapper = ModuleDeprecationWrapper(__name__)
wrapper._add_deprecated_attr('User', replacement_name='pywikibot.User')
