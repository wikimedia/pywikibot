"""Folder which holds framework scripts.

When uploading pywikibot to pypi the pwb.py (wrapper script) and
pywikibot i18n package are copied here.

.. versionadded:: 7.0
"""
#
# (C) Pywikibot team, 2021-2022
#
# Distributed under the terms of the MIT license
#
from os import environ, getenv


def _import_with_no_user_config(*import_args):
    """Return ``__import__(*import_args)`` without loading user config.

    .. versionadded:: 3.0
    .. versionchanged:: 7.0
       moved to pywikibot.scripts
    """
    orig_no_user_config = getenv('PYWIKIBOT_NO_USER_CONFIG')
    environ['PYWIKIBOT_NO_USER_CONFIG'] = '2'
    result = __import__(*import_args)
    # Reset this flag
    if not orig_no_user_config:
        del environ['PYWIKIBOT_NO_USER_CONFIG']
    else:
        environ['PYWIKIBOT_NO_USER_CONFIG'] = orig_no_user_config
    return result
