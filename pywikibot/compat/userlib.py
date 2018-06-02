# -*- coding: utf-8 -*-
"""
WARNING: THIS MODULE EXISTS SOLELY TO PROVIDE BACKWARDS-COMPATIBILITY.

Do not use in new scripts; use the source to find the appropriate
function/method instead.

"""
#
# (C) Pywikibot team, 2008-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot.page import User
from pywikibot.tools import ModuleDeprecationWrapper

__all__ = ('User',)

wrapper = ModuleDeprecationWrapper(__name__)
wrapper._add_deprecated_attr('User', replacement_name='pywikibot.User')
