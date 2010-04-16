""" Module with the graphviz drawing calls """
#
# (C) Pywikipedia bot team, 2006-2010
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
import threading
pydotfound = True
try:
    import pydot
except ImportError:
    pydotfound = False
import pywikibot
from pywikibot import config2 as config

# for speedyshare
import re
import httplib, urllib2, mimetypes

class GraphImpossible(Exception):
    "Drawing a graph is not possible on your system."

class GraphSavingThread(threading.Thread):
    """
    Rendering a graph can take extremely long. We use
    multithreading because of that.

    TODO: Find out if several threads running in parallel
    can slow down the system too much. Consider adding a
    mechanism to kill a thread if it takes too long.
    """

    def __init__(self, graph, originPage):
        threading.Thread.__init__(self)
        self.graph = graph
        self.originPage = originPage

    def run(self):
        for format in config.interwiki_graph_formats:
            filename = 'interwiki-graphs/' + getFilename(self.originPage,
                                                         format)
            if self.graph.write(filename, prog = 'dot', format = format):
                pywikibot.output(u'Graph saved as %s' % filename)
            else:
                pywikibot.output(u'Graph could not be saved as %s' % filename)

class GraphDrawer:
    def __init__(self, subject):
        if not pydotfound:
            raise GraphImpossible, 'pydot is not installed.'
        self.graph = None
        self.subject = subject

    def getLabel(self, page):
        return (u'"\"%s:%s\""' % (page.site().language(),
                                  page.title())).encode('utf-8')

    def addNode(self, page):
        node = pydot.Node(self.getLabel(page), shape = 'rectangle')
        node.set_URL("\"http://%s%s\""
                     % (page.site().hostname(),
                        page.site().get_address(page.urlname())))
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
        # if we found more than one valid page for this language:
        if len(filter(lambda p: p.site() == page.site() and p.exists() \
                      and not p.isRedirectPage(),
                      self.subject.foundIn.keys())) > 1:
            # mark conflict by octagonal node
            node.set_shape('octagon')
        self.graph.add_node(node)

    def addDirectedEdge(self, page, refPage):
        # if page was given as a hint, referrers would be [None]
        if refPage is not None:
            sourceLabel = self.getLabel(refPage)
            targetLabel = self.getLabel(page)
            edge = pydot.Edge(sourceLabel, targetLabel)
            oppositeEdge = self.graph.get_edge(targetLabel, sourceLabel)
            if oppositeEdge:
                #oppositeEdge.set_arrowtail('normal')
                oppositeEdge.set_dir('both')
            # workaround for bug [ 1722739 ]: prevent duplicate edges
            # (it is unclear why duplicate edges occur)
            elif self.graph.get_edge(sourceLabel, targetLabel):
                pywikibot.output(
                    u'BUG: Tried to create duplicate edge from %s to %s'
                    % (refPage.title(asLink=True), page.title(asLink=True)))
                # duplicate edges would be bad because then get_edge() would
                # give a list of edges, not a single edge when we handle the
                # opposite edge.
            else:
                # add edge
                if refPage.site() == page.site():
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
        thread = GraphSavingThread(self.graph, self.subject.originPage)
        thread.start()

    def createGraph(self):
        """
        See http://meta.wikimedia.org/wiki/Interwiki_graphs
        """
        pywikibot.output(u'Preparing graph for %s'
                         % self.subject.originPage.title())
        # create empty graph
        self.graph = pydot.Dot()
        # self.graph.set('concentrate', 'true')
        for page in self.subject.foundIn.iterkeys():
            # a node for each found page
            self.addNode(page)
        # mark start node by pointing there from a black dot.
        firstLabel = self.getLabel(self.subject.originPage)
        self.graph.add_node(pydot.Node('start', shape = 'point'))
        self.graph.add_edge(pydot.Edge('start', firstLabel))
        for page, referrers in self.subject.foundIn.iteritems():
            for refPage in referrers:
                self.addDirectedEdge(page, refPage)
        self.saveGraphFile()

class SpeedyShareUploader:
    def __init__(self):
        pass

    def getToken(self):
        formR = re.compile(
            '<form target=_top method="post" action="upload\.php\?(\d+)"')

        uploadPage = urllib2.urlopen(
            'http://www.speedyshare.com/index_upload.php')
        text = uploadPage.read()
        token = formR.search(text).group(1)
        return token

    def post_multipart(self, host, selector, fields, files):
        """
        Post fields and files to an http host as multipart/form-data.
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, value) elements for data to be
        uploaded as files. Return the server's response page.
        """
        content_type, body = self.encode_multipart_formdata(fields, files)
        h = httplib.HTTP(host)
        h.putrequest('POST', selector)
        h.putheader('Content-Type', content_type)
        h.putheader('Content-Length', str(len(body)))
        h.putheader('User-Agent',
                    'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.8) Gecko/20051128 SUSE/1.5-0.1 Firefox/1.5')
        h.putheader('Referer', 'http://www.speedyshare.com/index_upload.php')
        h.putheader('Accept',
                    'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5')
        h.putheader('Accept-Language', 'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3')
        h.putheader('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7')
        h.putheader('Keep-Alive', '30')
        h.putheader('Connection', 'keep-alive')

        h.endheaders()
        h.send(body)
        errcode, errmsg, headers = h.getreply()
        return errcode, h.file.read()

    def encode_multipart_formdata(self, fields, files):
        """
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, value) elements for data to be
        uploaded as files. Return (content_type, body) ready for httplib.HTTP
        instance
        """
        BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
        CRLF = '\r\n'
        L = []
        for (key, value) in fields:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            L.append(value)
        for (key, filename, value) in files:
            L.append('--' + BOUNDARY)
            L.append(
                'Content-Disposition: form-data; name="%s"; filename="%s"'
                % (key, filename))
            L.append('Content-Type: %s' % self.get_content_type(filename))
            L.append('')
            L.append(value)
        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
        return content_type, body

    def get_content_type(self, filename):
        return mimetypes.guess_type(filename)[0] \
               or 'application/octet-stream'

    def upload(self, filename):
        token = self.getToken()

        file = open(filename)
        encodedFilename = filename#.encode('utf-8')
        contents = file.read()
        formdata = []

        response, returned_html = self.post_multipart('www.speedyshare.com',
                                  'upload.php?' + token,
                                  formdata,
                                  [('fileup0', encodedFilename, contents)])
        print response
        print returned_html


def getFilename(page, extension = None):
    filename = '%s-%s-%s' % (page.site().family.name,
                             page.site().language(),
                             page.titleForFilename())
    if extension:
        filename += '.%s' % extension
    return filename

if __name__ == "__main__":
    uploader = SpeedyShareUploader()
    uploader.upload(
        '/home/daniel/projekte/pywikipedia/interwiki-graphs/wikipedia-de-CEE.svg')
