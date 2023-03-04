#!/usr/bin/env python3
r"""Visualizes category hierarchy.

Generates graphical representation in formats dot, svg and html5
of category hierarchy.

Usage:

    pwb.py graph [-style STYLE] [-depth DEPTH] [-from FROM] [-to TO]

actions:

-from [FROM]   Category name to scan, default is main category, "?" to ask.

optional arguments:

-to TO         base file name to save, "?" to ask
-style STYLE   graphviz style definitions in dot format (see below)
-depth DEPTH   maximal hierarchy depth. 2 by default
-downsize K    font size divider for subcategories. 4 by default
               Use 1 for the same font size

.. seealso:: https://graphviz.org/doc/info/attrs.html
   for graphviz style definitions.

Example::

    pwb.py -v category_graph -from

Extended example with style settings::

    pwb.py category_graph -from Life -downsize 1.5 \
    -style 'graph[rankdir=BT ranksep=0.5] node[shape=circle
    style=filled fillcolor=green] edge[style=dashed penwidth=3]'

.. versionadded:: 8.0
"""
#
# (C) Pywikibot team, 2022-2023
#
# Distributed under the terms of the MIT license.
#
import argparse
from collections import defaultdict

import pywikibot
from pywikibot import config
from pywikibot.bot import SingleSiteBot, suggest_help


class CategoryGraphBot(SingleSiteBot):
    """Bot to create graph of the category structure."""

    def args(self, ap):
        """Declares arguments."""
        ap.add_argument('-from', nargs='?', default=argparse.SUPPRESS)
        ap.add_argument('-to', nargs='?', default='')
        ap.add_argument('-style', nargs='?', default='')
        ap.add_argument('-depth', nargs='?', default=2)
        ap.add_argument('-downsize', nargs='?', default=4)

    def __init__(self, ap, args: argparse.Namespace) -> None:
        """Initializer."""
        super().__init__()
        self.args = args
        cat_title = args.__dict__.get('from')
        if not cat_title:
            cat_title = 'Main topic classifications'
        if cat_title == '?':
            cat_title = pywikibot.input(
                'For which category do you want to create a graph?')

        pywikibot.info('Scanning {cat_title!r}')
        self.cat = pywikibot.Category(self.site, cat_title)
        self.to = args.to
        if self.to == '?':
            self.to = pywikibot.input(
                'Please enter the name of the file '
                'where the tree should be saved,\n'
                'or press enter to use category name:')
        if not self.to:
            self.to = cat_title.replace(' ', '_')
        self.rev = defaultdict(list)
        self.fw = defaultdict(list)
        self.leaves = set()
        self.counter = 0
        font = 'fontname="Helvetica,Arial,sans-serif"'
        style = f'graph [rankdir=LR ranksep=2 concentrate=true {font}] ' \
                f'node [newrank=true shape=plaintext {font}] ' \
                f'edge [arrowhead=open labeldistance=3 ' \
                f'labelfontcolor="#00000080" {font}] ' + args.style
        self.dot = pydot.graph_from_dot_data(f'digraph {style}')[0]
        self.dot.set_name(f'"{cat_title}"')

    def scan_level(self, cat, level, hue=None) -> str:
        """Recursive function to fill dot graph.

        :param cat: the Category of the node we're currently opening.
        :param level: the current decreasing from depth to zero level in
            the tree (for recursion), opposite of depth.
        """
        title = cat.title(with_ns=False)
        size = float(args.downsize) ** level
        subcats = sorted(cat.subcategories())

        def node():
            subs = ', '.join([c.title(with_ns=False).replace(' ', '&nbsp;')
                              for c in subcats])
            n = pydot.Node(title,
                           label=rf'"{title}\n{len(subcats)} C"',
                           tooltip=title + '\n\n' + subs,
                           URL=cat.full_url(),
                           fontsize=int(10 * size))
            return n

        def edge(n, h):
            minlen = n % columns + 1 if level != self.args.depth else 1
            e = pydot.Edge(title,
                           subcat.title(with_ns=False),
                           tooltip=title + '  ⟶  '
                           + subcat.title(with_ns=False),
                           headlabel=title,
                           # distribute the graph to depth
                           minlen=minlen,
                           penwidth=round(size / 2, 2),
                           arrowsize=round(size / 4, 2),
                           color=str(round(h, 2)) + ' 1 0.7',
                           labelfontsize=int(3 * size),
                           labelfontcolor=str(round(h, 2)) + ' 1 0.5')
            return e

        if config.verbose_output:
            pywikibot.info('Adding ' + cat.title(with_ns=False))

        node = node()
        self.dot.add_node(node)
        self.counter += 1
        if not level or self.counter >= 1e4:
            # because graphviz crashes on huge graphs
            if self.counter == 1e4:
                pywikibot.warning('Number of nodes reached limit')
            self.leaves.add(node.get_name())
            return

        columns = len(subcats) // 5 + 1
        for n, subcat in enumerate(subcats):
            # generating different hue for color per each root branch
            h = hue if hue is not None else (11 / 18 * n) % 1
            e = edge(n, h)
            self.dot.add_edge(e)
            # repeat recursively
            self.scan_level(subcat, level - 1, h)
            # track graph's structure to reduse too big graph
            self.rev[e.get_destination()].append(e.get_source())
            self.fw[e.get_source()].append(e.get_destination())

    def run(self) -> None:
        """Main function of CategoryGraphBot."""
        self.scan_level(self.cat, int(self.args.depth))
        # reduce too big graph
        if self.counter > 1000:
            pywikibot.warning('Removing standalone subcategories '
                              'because graph is too big')
            for n in self.leaves:
                while len(self.rev[n]) == 1:
                    if config.verbose_output:
                        pywikibot.info('Removing ' + n)

                    self.dot.del_edge(self.rev[n][0], n)
                    self.dot.del_node(n)
                    self.fw[self.rev[n][0]].remove(n)
                    if self.fw[self.rev[n][0]]:
                        break
                    n = self.rev[n][0]

        pywikibot.info('Saving results')
        pywikibot.info(self.to + '.gv')
        self.dot.write(self.to + '.gv', encoding='utf-8')
        pywikibot.info(self.to + '.svg')
        self.dot.write_svg(self.to + '.svg', encoding='utf-8')
        pywikibot.info(self.to + '.html')

        header = ('<head><meta charset="UTF-8"/>'
                  '<title>' + self.cat.title(with_ns=False)
                  + '</title> </head>\n'
                  '<div style="position:absolute;">'
                  'Zoom and drag with mouse. '
                  'Nodes are links to Wikipedia.'
                  '</div>\n'
                  '<script '
                  'src="https://unpkg.com/panzoom@9.4.0/dist/panzoom.min.js" '
                  'query="#graph0" name="pz"></script>\n'
                  '<style> svg { height:100%; width:100%; } </style>\n')
        with open(self.to + '.html', mode='wb') as o:
            o.write(header.encode())
            o.write(self.dot.create('dot', 'svg', encoding='utf-8'))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(add_help=False)
    CategoryGraphBot.args(None, ap)
    local_args = pywikibot.handle_args()
    args, rest = ap.parse_known_args()

    if not suggest_help(missing_action='from' not in args):
        import pydot
        bot = CategoryGraphBot(ap, args)
        bot.run()
