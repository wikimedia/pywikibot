#!/usr/bin/env python3
"""Utility to show pywikibot colors."""
#
# (C) Pywikibot team, 2016-2022
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot.tools.itertools import itergroup
from pywikibot.userinterfaces.terminal_interface_base import colors


def main():
    """Main function."""
    fg_colors = [col for col in colors if col != 'default']
    bg_colors = fg_colors[:]
    n_fg_colors = len(fg_colors)
    fg_colors.insert(3 * int(n_fg_colors / 4), 'default')
    fg_colors.insert(2 * int(n_fg_colors / 4), 'default')
    fg_colors.insert(int(n_fg_colors / 4), 'default')
    fg_colors.insert(0, 'default')

    # Max len of color names for padding.
    max_len_fg_colors = len(max(fg_colors, key=len))
    max_len_bc_color = len(max(bg_colors, key=len))

    for bg_col in bg_colors:
        # Three lines per each backgoung color.
        for fg_col_group in itergroup(fg_colors, n_fg_colors / 4 + 1):
            line = ''
            for fg_col in fg_col_group:
                line += ' '
                line += '<<{color}>>{}<<default>>'.format(
                    fg_col.ljust(max_len_fg_colors),
                    color=f'{fg_col};{bg_col}')

            line = f'{bg_col.ljust(max_len_bc_color)} {line}'
            pywikibot.info(line)

        pywikibot.info()


if __name__ == '__main__':
    main()
