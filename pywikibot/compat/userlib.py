# -*- coding: utf-8 -*-
"""
WARNING: THIS MODULE EXISTS SOLELY TO PROVIDE COMPAT BACKWARDS-COMPATIBILITY.

IT IS DEPRECATED. DO NOT USE IT.

Do not use this module anymore; use pywikibot.User instead.
"""
#
# (C) Pywikibot team, 2008-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot.page import User
from pywikibot.tools import ModuleDeprecationWrapper

__all__ = ('User',)

wrapper = ModuleDeprecationWrapper(__name__)
wrapper._add_deprecated_attr('User',
                             replacement_name='pywikibot.User',
                             since='20141209', future_warning=True)
