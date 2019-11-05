# -*- coding: utf-8 -*-
"""Module with the Graphviz drawing calls."""
#
# (C) Pywikibot team, 2006-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from collections import Counter
import itertools
import threading

try:
    import pydot
except ImportError as e:
    pydot = e

import pywikibot

from pywikibot import config2 as config

# deprecated value
pydotfound = not isinstance(pydot, ImportError)


class GraphImpossible(Exception):

    """Drawing a graph is not possible on your system."""


class GraphSavingThread(threading.Thread):

    """
    Threaded graph renderer.

    Rendering a graph can take extremely long. We use
    multithreading because of that.

    TODO: Find out if several threads running in parallel
    can slow down the system too much. Consider adding a
    mechanism to kill a thread if it takes too long.
    """

    def __init__(self, graph, originPage):
        """Initializer."""
        threading.Thread.__init__(self)
        self.graph = graph
        self.originPage = originPage

    def run(self):
        """Write graphs to the data directory."""
        for format in config.interwiki_graph_formats:
            filename = config.datafilepath(
                'interwiki-graphs/' + getFilename(self.originPage, format))
            if self.graph.write(filename, prog='dot', format=format):
                pywikibot.output('Graph saved as %s' % filename)
            else:
                pywikibot.output('Graph could not be saved as %s' % filename)


class Subject(object):

    """Data about a page with translations on multiple wikis."""

    def __init__(self, origin=None):
        """Initializer.

        @param originPage: the page on the 'origin' wiki
        @type originPage: pywikibot.page.Page
        """
        # Remember the "origin page"
        self._origin = origin

        # Temporary variable to support git blame; do not use
        originPage = origin

        self.found_in = None

        # foundIn is a dictionary where pages are keys and lists of
        # pages are values. It stores where we found each page.
        # As we haven't yet found a page that links to the origin page, we
        # start with an empty list for it.
        if originPage:
            self.foundIn = {self.originPage: []}
        else:
            self.foundIn = {}

    @property
    def origin(self):
        """Page on the origin wiki."""
        return self._origin

    @origin.setter
    def origin(self, value):
        self._origin = value

    @property
    def originPage(self):
        """Deprecated property for the origin page.

        DEPRECATED. Use origin.
        """
        # TODO: deprecate this property
        return self.origin

    @originPage.setter
    def originPage(self, value):
        self.origin = value

    @property
    def foundIn(self):
        """Mapping of pages to others pages interwiki linked to it.

        DEPRECATED. Use found_in.
        """
        # TODO: deprecate this property
        return self.found_in

    @foundIn.setter
    def foundIn(self, value):
        """Temporary property setter to support code migration."""
        self.found_in = value


class GraphDrawer(object):

    """Graphviz (dot) code creator."""

    def __init__(self, subject):
        """Initializer.

        @param subject: page data to graph
        @type subject: pywikibot.interwiki_graph.Subject

        @raises GraphImpossible: pydot is not installed
        """
        if isinstance(pydot, ImportError):
            raise GraphImpossible('pydot is not installed: %s.' % pydot)
        self.graph = None
        self.subject = subject

    def getLabel(self, page):
        """Get label for page."""
        return '"%s:%s"' % (page.site.code, page.title())

    def _octagon_site_set(self):
        """Build a list of sites with more than one valid page."""
        page_list = self.subject.found_in.keys()

        # Only track sites of normal pages
        each_site = [page.site for page in page_list
                     if page.exists() and not page.isRedirectPage()]

        return {x[0] for x in itertools.takewhile(
            lambda x: x[1] > 1,
            Counter(each_site).most_common())}

    def addNode(self, page):
        """Add a node for page."""
        node = pydot.Node(self.getLabel(page), shape='rectangle')
        node.set_URL('"http://%s%s"'
                     % (page.site.hostname(),
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
        if page.namespace() != self.subject.originPage.namespace():
            node.set_color('green')
            node.set_style('filled,bold')
        if page.site in self.octagon_sites:
            # mark conflict by octagonal node
            node.set_shape('octagon')
        self.graph.add_node(node)

    def addDirectedEdge(self, page, refPage):
        """Add a directed edge from refPage to page."""
        # if page was given as a hint, referrers would be [None]
        if refPage is not None:
            sourceLabel = self.getLabel(refPage)
            targetLabel = self.getLabel(page)
            edge = pydot.Edge(sourceLabel, targetLabel)

            oppositeEdge = self.graph.get_edge(targetLabel, sourceLabel)
            if oppositeEdge:
                if isinstance(oppositeEdge, list):
                    # bugfix for pydot >= 1.0.3
                    oppositeEdge = oppositeEdge[0]
                oppositeEdge.set_dir('both')
            # workaround for sf.net bug 401: prevent duplicate edges
            # (it is unclear why duplicate edges occur)
            # https://sourceforge.net/p/pywikipediabot/bugs/401/
            elif self.graph.get_edge(sourceLabel, targetLabel):
                pywikibot.output(
                    'BUG: Tried to create duplicate edge from %s to %s'
                    % (refPage.title(as_link=True), page.title(as_link=True)))
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

    def saveGraphFile(self):
        """Write graphs to the data directory."""
        thread = GraphSavingThread(self.graph, self.subject.originPage)
        thread.start()

    def createGraph(self):
        """
        Create graph of the interwiki links.

        For more info see U{https://meta.wikimedia.org/wiki/Interwiki_graphs}
        """
        pywikibot.output('Preparing graph for %s'
                         % self.subject.originPage.title())
        # create empty graph
        self.graph = pydot.Dot()
        # self.graph.set('concentrate', 'true')

        self.octagon_sites = self._octagon_site_set()

        for page in self.subject.foundIn.keys():
            # a node for each found page
            self.addNode(page)
        # mark start node by pointing there from a black dot.
        firstLabel = self.getLabel(self.subject.originPage)
        self.graph.add_node(pydot.Node('start', shape='point'))
        self.graph.add_edge(pydot.Edge('start', firstLabel))
        for page, referrers in self.subject.foundIn.items():
            for refPage in referrers:
                self.addDirectedEdge(page, refPage)
        self.saveGraphFile()


def getFilename(page, extension=None):
    """
    Create a filename that is unique for the page.

    @param page: page used to create the new filename
    @type page: pywikibot.page.Page
    @param extension: file extension
    @type extension: str
    @return: filename of <family>-<lang>-<page>.<ext>
    @rtype: str
    """
    filename = '%s-%s-%s' % (page.site.family.name,
                             page.site.code,
                             page.title(as_filename=True))
    if extension:
        filename += '.%s' % extension
    return filename
