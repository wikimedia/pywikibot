"""Configuration file for pytest.

.. versionadded:: 10.3
"""
#
# (C) Pywikibot team, 2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import re
from pathlib import Path
from typing import Literal


EXCLUDE_PATTERN = re.compile(
    r'(?:'
    r'(__metadata__|backports|config|cosmetic_changes|daemonize|diff|echo|'
    r'exceptions|fixes|logging|plural|time|titletranslate)|'
    r'(comms|data|families|specialbots)/__init__|'
    r'comms/eventstreams|'
    r'data/(api/(__init__|_optionset)|citoid|memento|wikistats)|'
    r'families/[a-z][a-z\d]+_family|'
    r'page/(__init__|_decorators|_page|_revision|_user)|'
    r'pagegenerators/(__init__|_filters)|'
    r'scripts/(i18n/)?__init__|'
    r'site/(__init__|_basesite|_decorators|_interwikimap|'
    r'_tokenwallet|_upload)|'
    r'tools/(_deprecate|_logging|_unidata|chars|formatter|itertools)|'
    r'userinterfaces/(__init__|_interface_base|buffer_interface|'
    r'terminal_interface|transliteration)'
    r')\.py'
)


def pytest_ignore_collect(collection_path: Path,
                          config) -> Literal[True] | None:
    """Ignore files matching EXCLUDE_PATTERN when pytest-mypy is loaded."""
    # Check if any plugin name includes 'mypy'
    plugin_names = {p.__class__.__name__.lower()
                    for p in config.pluginmanager.get_plugins()}
    if not any('mypy' in name for name in plugin_names):
        return None

    # no cover: start
    project_root = Path(__file__).parent / 'pywikibot'
    try:
        rel_path = collection_path.relative_to(project_root)
    except ValueError:
        # Ignore files outside project root
        return None

    norm_path = rel_path.as_posix()
    if EXCLUDE_PATTERN.fullmatch(norm_path):
        print(f'Ignoring file in mypy: {norm_path}')  # noqa: T201
        return True

    return None
    # no cover: stop
