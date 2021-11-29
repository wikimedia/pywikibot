"""Folder which holds framework scripts.

When uploading pywikibot to pypi the pwb.py (wrapper script) is copied here.

.. versionadded:: 7.0
"""
from os import environ, getenv


def _import_with_no_user_config(*import_args: str):
    """Return __import__(*import_args) without loading user-config.py.

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
