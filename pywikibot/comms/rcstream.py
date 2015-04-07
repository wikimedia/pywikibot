"""
SocketIO-based rcstream client.

(c) 2014 Merlijn van Deen

This file is part of the Pywikibot framework, and is licensed under the MIT license.

This module requires socketIO_client to be installed:
    pip install socketIO_client
"""
from __future__ import unicode_literals

import sys
import threading

if sys.version_info[0] > 2:
    from queue import Queue, Empty
else:
    from Queue import Queue, Empty

from pywikibot.bot import debug, warning

_logger = 'pywikibot.rcstream'


class RcListenerThread(threading.Thread):

    """
    Low-level RC Listener Thread, which reads the RC stream and pushes them to it's internal queue.

    @param wikihost: the hostname of the wiki we want to get changes for. This
                     is passed to rcstream using a 'subscribe' command. Pass
                     '*' to listen to all wikis for a given rc host.
    @param rchost: the recent changes stream host to connect to. For Wikimedia
                   wikis, this is 'stream.wikimedia.org'
    @param rcport: the port to connect to (default: 80)
    @param rcpath: the sockets.io path. For Wikimedia wikis, this is '/rc'.
                   (default: '/rc')
    @param total:  the maximum number of entries to return. The underlying
                   thread is shut down then this number is reached.

    This part of the rc listener runs in a Thread. It makes the actual
    socketIO/websockets connection to the rc stream server, subscribes
    to a single site and pushes those entries into a queue.

    Usage:
    >>> t = RcListenerThread('en.wikipedia.org', 'stream.wikimedia.org')
    >>> t.start()
    >>> change = t.queue.get()
    >>> change
    {'server_name': 'en.wikipedia.org', 'wiki': 'enwiki', 'minor': True,
     'length': {'new': 2038, 'old': 2009}, 'timestamp': 1419964350,
     'server_script_path': '/w', 'bot': False, 'user': 'Od Mishehu',
     'comment': 'stub sorting', 'title': 'Bradwell Bay Wilderness',
     'server_url': 'http://en.wikipedia.org', 'id': 703158386,
     'revision': {'new': 640271171, 'old': 468264850},
     'type': 'edit', 'namespace': 0}
    >>> t.stop()  # optional, the thread will shut down on exiting python as well
    """

    def __init__(self, wikihost, rchost, rcport=80, rcpath='/rc', total=None):
        """Constructor for RcListenerThread."""
        super(RcListenerThread, self).__init__()
        self.rchost = rchost
        self.rcport = rcport
        self.rcpath = rcpath
        self.wikihost = wikihost

        self.daemon = True
        self.running = False
        self.queue = Queue()

        self.warn_queue_length = 100

        self.total = total
        self.count = 0

        import socketIO_client
        debug('Opening connection to %r' % self, _logger)
        self.client = socketIO_client.SocketIO(rchost, rcport)

        thread = self

        class RCListener(socketIO_client.BaseNamespace):
            def on_change(self, change):
                debug('Received change %r' % change, _logger)
                if not thread.running:
                    debug('Thread in shutdown mode; ignoring change.', _logger)
                    return

                thread.count += 1
                thread.queue.put(change)
                if thread.queue.qsize() > thread.warn_queue_length:
                    warning('%r queue length exceeded %i'
                            % (thread,
                               thread.warn_queue_length),
                            _logger=_logger)
                    thread.warn_queue_length = thread.warn_queue_length + 100

                if thread.total is not None and thread.count >= thread.total:
                    thread.stop()
                    return

            def on_connect(self):
                debug('Connected to %r; subscribing to %s'
                          % (thread, thread.wikihost),
                      _logger)
                self.emit('subscribe', thread.wikihost)
                debug('Subscribed to %s' % thread.wikihost, _logger)

            def on_reconnect(self):
                debug('Reconnected to %r' % (thread,), _logger)
                self.on_connect()

        class GlobalListener(socketIO_client.BaseNamespace):
            def on_heartbeat(self):
                self._transport.send_heartbeat()

        self.client.define(RCListener, rcpath)
        self.client.define(GlobalListener)

    def __repr__(self):
        """Return representation."""
        return "<rcstream for socketio://%s@%s:%s%s>" % (
               self.wikihost, self.rchost, self.rcport, self.rcpath
        )

    def run(self):
        """Threaded function. Runs insided the thread when started with .start()."""
        self.running = True
        while self.running:
            self.client.wait(seconds=0.1)
        debug('Shut down event loop for %r' % self, _logger)
        self.client.disconnect()
        debug('Disconnected %r' % self, _logger)
        self.queue.put(None)

    def stop(self):
        """Stop the thread."""
        self.running = False


def rc_listener(wikihost, rchost, rcport=80, rcpath='/rc', total=None):
    """RC Changes Generator. Yields changes received from RCstream.

    @param wikihost: the hostname of the wiki we want to get changes for. This
                     is passed to rcstream using a 'subscribe' command. Pass
                     '*' to listen to all wikis for a given rc host.
    @param rchost: the recent changes stream host to connect to. For Wikimedia
                   wikis, this is 'stream.wikimedia.org'
    @param rcport: the port to connect to (default: 80)
    @param rcpath: the sockets.io path. For Wikimedia wikis, this is '/rc'.
                   (default: '/rc')
    @param total: the maximum number of entries to return. The underlying thread
                  is shut down then this number is reached.

    @yields dict: dict as formatted by MediaWiki's MachineReadableRCFeedFormatter[1],
                  which consists of at least id (recent changes id), type ('edit',
                  'new', 'log' or 'external'), namespace, title, comment, timestamp,
                  user and bot (bot flag for the change). See [1] for more details.

    @raises ImportError

    [1] https://github.com/wikimedia/mediawiki/blob/master/includes/rcfeed/MachineReadableRCFeedFormatter.php

    """
    try:
        # this is just to test whether socketIO_client is installed or not,
        # as the ImportError would otherwise pop up in the worker thread
        # where it's not easily caught. We don't use it, so we silence
        # flake8 with noqa.
        import socketIO_client  # noqa
    except ImportError:
        raise ImportError('socketIO_client is required for the rc stream; '
                          'install it with pip install socketIO_client')

    rc_thread = RcListenerThread(
        wikihost=wikihost,
        rchost=rchost, rcport=rcport, rcpath=rcpath,
        total=total
    )

    debug('Starting rcstream thread %r' % rc_thread,
          _logger)
    rc_thread.start()

    while True:
        try:
            element = rc_thread.queue.get(timeout=0.1)
        except Empty:
            continue
        if element is None:
            return
        yield element


def site_rc_listener(site, total=None):
    """RC Changes Generator. Yields changes received from RCstream.

    @param site: the Pywikibot.Site object to yield live recent changes for
    @type site: Pywikibot.BaseSite
    @param total: the maximum number of changes to return
    @type total: int

    @returns pywikibot.comms.rcstream.rc_listener configured for the given site
    """
    return rc_listener(
        wikihost=site.hostname(),
        rchost=site.rcstream_host(),
        total=total,
    )
