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
__version__ = '$Id$'


from pywikibot import Category


def change_category(article, oldCat, newCat, comment=None, sortKey=None,
                    inPlace=True):
    return article.change_category(oldCat, newCat, comment, sortKey, inPlace)

__all__ = ('Category', 'change_category',)
