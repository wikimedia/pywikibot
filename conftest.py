"""Configuration file for pytest."""
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
    r'(__metadata__|exceptions|fixes|time)|'
    r'(comms|data|families|specialbots)/__init__|'
    r'families/[a-z]+_family|'
    r'page/(__init__|_decorators|_revision)|'
    r'scripts/(i18n/)?__init__|'
    r'site/(__init__|_basesite|_decorators|_interwikimap|_upload)|'
    r'tools/(_logging|_unidata|formatter)|'
    r'userinterfaces/(__init__|_interface_base|terminal_interface)'
    r')\.py'
)


def pytest_ignore_collect(collection_path: Path,
                          config) -> Literal[True] | None:
    """Ignore files matching EXCLUDE_PATTERN when pytest-mypy is loaded.

    .. versionadded:: 10.3
    """
    # Check if any plugin name includes 'mypy'
    plugin_names = {p.__class__.__name__.lower()
                    for p in config.pluginmanager.get_plugins()}
    if not any('mypy' in name for name in plugin_names):
        return None

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
