"""**Scripts** folder contains predefined scripts easy to use.

Scripts are only available with Pywikibot if installed in directory mode
and not as site package. They can be run in command line using the pwb
wrapper script::

    python pwb.py <global options> <name_of_script> <options>


Every script provides a ``-help`` option which shows all available
options, their explanation and usage examples. :ref:`Global options`
will be shown by ``-help:global`` or using::

    python pwb.py -help

The advantages of pwb.py wrapper script are:

- check for framework and script depedencies and show a warning if a
  package is missing or outdated or if the Python release does not fit
- check whether user config file (user-config.py) is available and ask
  to create it by starting the generate_user_files.py script
- enable global options even if a script does not support them
- start private scripts located in userscripts sub-folder
- find a script even if given script name does not match a filename e.g.
  due to spelling mistake
"""
#
# (C) Pywikibot team, 2021-2023
#
# Distributed under the terms of the MIT license.
#
__version__ = '8.1.0'
