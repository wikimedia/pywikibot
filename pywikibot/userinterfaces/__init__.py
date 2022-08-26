"""User interfaces module.

The user interface object must define its own `init_handlers()` method
which takes the root logger as its only argument, and which adds to that
logger whatever handlers and formatters are needed to process output and
display it to the user. The default
(:mod:`terminal<userinterfaces.terminal_interface_base>`)
interface sends level :const:`STDOUT` to `sys.stdout` (as all interfaces
should) and sends all other levels to `sys.stderr`; levels
:const:`WARNING` and above are labeled with the level name.

UserInterface objects must also define methods `input()`,
`input_choice()`, `input_list_choice()`, `output()` and `editText()`,
all of which are documented in the abstract class
:class:`userinterfaces._interface_base.ABUIC`.
"""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
