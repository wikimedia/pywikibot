"""Module with the Graphviz drawing calls."""
#
# (C) Pywikibot team, 2006-2022
#
# Distributed under the terms of the MIT license.
#
import itertools
import threading
from collections import Counter
from typing import Optional

import pywikibot
from pywikibot import config
from pywikibot.backports import Dict, List, Set


try:
    import pydot
    PYDOT_ERROR = None
except ImportError as e:
    PYDOT_ERROR = e


FoundInType = Dict['pywikibot.page.Page', List['pywikibot.page.Page']]


class GraphSavingThread(threading.Thread):

    """
    Threaded graph renderer.

    Rendering a graph can take extremely long. We use
    multithreading because of that.

    TODO: Find out if several threads running in parallel
    can slow down the system too much. Consider adding a
    mechanism to kill a thread if it takes too long.
    """

    def __init__(self, graph: 'pydot.Dot',
                 origin: 'pywikibot.page.Page') -> None:
        """Initializer."""
        super().__init__()
        self.graph = graph
        self.origin = origin

    def run(self) -> None:
        """Write graphs to the data directory."""
        for fmt in config.interwiki_graph_formats:
            filename = config.datafilepath(
                'interwiki-graphs/' + getFilename(self.origin, fmt))
            if self.graph.write(filename, prog='dot', format=fmt):
                pywikibot.info('Graph saved as ' + filename)
            else:
                pywikibot.info('Graph could not be saved as ' + filename)


class Subject:

    """Data about a page with translations on multiple wikis."""

    def __init__(self, origin: Optional['pywikibot.page.Page'] = None) -> None:
        """Initializer.

        :param origin: the page on the 'origin' wiki
        """
        # Remember the "origin page"
        self._origin = origin

        # found_in is a dictionary where pages are keys and lists of
        # pages are values. It stores where we found each page.
        # As we haven't yet found a page that links to the origin page, we
        # start with an empty list for it.
        self.found_in: FoundInType = {}
        if origin:
            self.found_in = {origin: []}

    @property
    def origin(self) -> Optional['pywikibot.page.Page']:
        """Page on the origin wiki."""
        return self._origin

    @origin.setter
    def origin(self, value: Optional['pywikibot.page.Page']) -> None:
        self._origin = value


class GraphDrawer:

    """Graphviz (dot) code creator."""

    def __init__(self, subject: 'pywikibot.interwiki_graph.Subject') -> None:
        """Initializer.

        :param subject: page data to graph

        :raises ImportError if pydot is not installed
        """
        if PYDOT_ERROR:
            msg = f'pydot is not installed: {PYDOT_ERROR}.'
            raise ImportError(msg)
        self.graph: Optional[pydot.Dot] = None
        self.subject = subject

    @staticmethod
    def getLabel(page: 'pywikibot.page.Page') -> str:
        """Get label for page."""
        return f'"{page.site.code}:{page.title()}"'

    def _octagon_site_set(self) -> Set['pywikibot.site.BaseSite']:
        """Build a list of sites with more than one valid page."""
        page_list = self.subject.found_in.keys()

        # Only track sites of normal pages
        each_site = (page.site for page in page_list
                     if page.exists() and not page.isRedirectPage())

        return {x[0] for x in itertools.takewhile(
            lambda x: x[1] > 1,
            Counter(each_site).most_common())}

    def addNode(self, page: 'pywikibot.page.Page') -> None:
        """Add a node for page."""
        assert self.graph is not None
        node = pydot.Node(self.getLabel(page), shape='rectangle')
        node.set_URL('"http://{}{}"'
                     .format(page.site.hostname(),
                             page.site.get_address(page.title(as_url=True))))
        node.set_style('filled')
        node.set_fillcolor('white')
        node.set_fontsize('11')
        if not page.exists():
            node.set_fillcolor('red')
        elif page.isRedirectPage():
            node.set_fillcolor('blue')
        elif page.isDisambig():
            node.set_fillcolor('orange')
        if page.namespace() != self.subject.origin.namespace():
            node.set_color('green')
            node.set_style('filled,bold')
        if page.site in self.octagon_sites:
            # mark conflict by octagonal node
            node.set_shape('octagon')
        self.graph.add_node(node)

    def addDirectedEdge(self, page: 'pywikibot.page.Page',
                        refPage: 'pywikibot.page.Page') -> None:
        """Add a directed edge from refPage to page."""
        assert self.graph is not None
        # if page was given as a hint, referrers would be [None]
        if refPage is not None:
            sourceLabel = self.getLabel(refPage)
            targetLabel = self.getLabel(page)
            edge = pydot.Edge(sourceLabel, targetLabel)

            oppositeEdge = self.graph.get_edge(targetLabel, sourceLabel)
            if oppositeEdge:
                oppositeEdge = oppositeEdge[0]
                oppositeEdge.set_dir('both')
            # workaround for sf.net bug 401: prevent duplicate edges
            # (it is unclear why duplicate edges occur)
            # https://sourceforge.net/p/pywikipediabot/bugs/401/
            elif self.graph.get_edge(sourceLabel, targetLabel):
                pywikibot.error(
                    'Tried to create duplicate edge from {} to {}'
                    .format(refPage, page))
                # duplicate edges would be bad because then get_edge() would
                # give a list of edges, not a single edge when we handle the
                # opposite edge.
            else:
                # add edge
                if refPage.site == page.site:
                    edge.set_color('blue')
                elif not page.exists():
                    # mark dead links
                    edge.set_color('red')
                elif refPage.isDisambig() != page.isDisambig():
                    # mark links between disambiguation and non-disambiguation
                    # pages
                    edge.set_color('orange')
                if refPage.namespace() != page.namespace():
                    edge.set_color('green')
                self.graph.add_edge(edge)

    def saveGraphFile(self) -> None:
        """Write graphs to the data directory."""
        assert self.graph is not None
        thread = GraphSavingThread(self.graph, self.subject.origin)
        thread.start()

    def createGraph(self) -> None:
        """
        Create graph of the interwiki links.

        For more info see https://meta.wikimedia.org/wiki/Interwiki_graphs
        """
        pywikibot.info('Preparing graph for {}'
                       .format(self.subject.origin.title()))
        # create empty graph
        self.graph = pydot.Dot()

        self.octagon_sites = self._octagon_site_set()

        for page in self.subject.found_in.keys():
            # a node for each found page
            self.addNode(page)
        # mark start node by pointing there from a black dot.
        firstLabel = self.getLabel(self.subject.origin)
        self.graph.add_node(pydot.Node('start', shape='point'))
        self.graph.add_edge(pydot.Edge('start', firstLabel))
        for page, referrers in self.subject.found_in.items():
            for refPage in referrers:
                self.addDirectedEdge(page, refPage)
        self.saveGraphFile()


def getFilename(page: 'pywikibot.page.Page',
                extension: Optional[str] = None) -> str:
    """
    Create a filename that is unique for the page.

    :param page: page used to create the new filename
    :param extension: file extension
    :return: filename of <family>-<lang>-<page>.<ext>
    """
    filename = '-'.join((page.site.family.name,
                         page.site.code,
                         page.title(as_filename=True)))
    if extension:
        filename += f'.{extension}'
    return filename
