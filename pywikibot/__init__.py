"""The initialization file for the Pywikibot framework."""
#
# (C) Pywikibot team, 2008-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import atexit
import datetime
import re
import sys
import threading
import warnings
from contextlib import suppress
from queue import Queue
from time import sleep as time_sleep
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlparse

from pywikibot import config as _config
from pywikibot import exceptions
from pywikibot.__metadata__ import __copyright__, __url__, __version__
from pywikibot._wbtypes import (
    Coordinate,
    WbGeoShape,
    WbMonolingualText,
    WbQuantity,
    WbTabularData,
    WbTime,
    WbUnknown,
)
from pywikibot.backports import Callable, cache, removesuffix
from pywikibot.bot import (
    Bot,
    CurrentPageBot,
    WikidataBot,
    calledModuleName,
    handle_args,
    input,
    input_choice,
    input_yn,
    show_help,
    ui,
)
from pywikibot.diff import PatchManager
from pywikibot.family import AutoFamily, Family
from pywikibot.i18n import translate
from pywikibot.logging import (
    critical,
    debug,
    error,
    exception,
    info,
    log,
    output,
    stdout,
    warning,
)
from pywikibot.site import BaseSite as _BaseSite
from pywikibot.time import Timestamp
from pywikibot.tools import normalize_username


if TYPE_CHECKING:
    from pywikibot.site import APISite


__all__ = (
    '__copyright__', '__url__', '__version__',
    'async_manager', 'async_request', 'Bot', 'calledModuleName', 'Category',
    'Claim', 'Coordinate', 'critical', 'CurrentPageBot', 'debug', 'error',
    'exception', 'FilePage', 'handle_args', 'html2unicode', 'info', 'input',
    'input_choice', 'input_yn', 'ItemPage', 'LexemeForm', 'LexemePage',
    'LexemeSense', 'Link', 'log', 'MediaInfo', 'output', 'Page',
    'page_put_queue', 'PropertyPage', 'showDiff', 'show_help', 'Site',
    'SiteLink', 'sleep', 'stdout', 'stopme', 'Timestamp', 'translate', 'ui',
    'User', 'warning', 'WbGeoShape', 'WbMonolingualText', 'WbQuantity',
    'WbTabularData', 'WbTime', 'WbUnknown', 'WikidataBot',
)

# argvu is set by pywikibot.bot when it's imported
if not hasattr(sys.modules[__name__], 'argvu'):
    argvu: list[str] = []

link_regex = re.compile(r'\[\[(?P<title>[^\]|[<>{}]*)(\|.*?)?\]\]')

_sites: dict[str, APISite] = {}


@cache
def _code_fam_from_url(url: str, name: str | None = None
                       ) -> tuple[str, str]:
    """Set url to cache and get code and family from cache.

    Site helper method.
    :param url: The site URL to get code and family
    :param name: A family name used by AutoFamily
    """
    matched_sites = []
    # Iterate through all families and look, which does apply to
    # the given URL
    for fam in _config.family_files:
        family = Family.load(fam)
        code = family.from_url(url)
        if code is not None:
            matched_sites.append((code, family))

    if not matched_sites:
        if not name:  # create a name from url
            name = urlparse(url).netloc.split('.')[-2]
            name = removesuffix(name, 'wiki')
        family = AutoFamily(name, url)
        matched_sites.append((family.code, family))

    if len(matched_sites) > 1:
        warning('Found multiple matches for URL "{}": {} (use first)'
                .format(url, ', '.join(str(s) for s in matched_sites)))
    return matched_sites[0]


def Site(code: str | None = None,  # noqa: N802
         fam: str | Family | None = None,
         user: str | None = None, *,
         interface: str | _BaseSite | None = None,
         url: str | None = None) -> _BaseSite:
    """A factory method to obtain a Site object.

    Site objects are cached and reused by this method.

    By default rely on config settings. These defaults may all be overridden
    using the method parameters.

    Creating the default site using config.mylang and config.family::

        site = pywikibot.Site()

    Override default site code::

        site = pywikibot.Site('fr')

    Override default family::

        site = pywikibot.Site(fam='wikisource')

    Setting a specific site::

        site = pywikibot.Site('fr', 'wikisource')

    which is equal to::

        site = pywikibot.Site('wikisource:fr')

    .. note:: An already created site is cached an a new variable points
       to the same object if interface, family, code and user are equal:

    >>> import pywikibot
    >>> site_1 = pywikibot.Site('wikisource:fr')
    >>> site_2 = pywikibot.Site('fr', 'wikisource')
    >>> site_1 is site_2
    True
    >>> site_1
    APISite('fr', 'wikisource')

    :class:`APISite<pywikibot.site._apisite.APISite>` is the default
    interface. Refer :py:obj:`pywikibot.site` for other interface types.

    .. warning:: Never create a site object via interface class directly.
       Always use this factory method.

    .. versionchanged:: 7.3
       Short creation if site code is equal to family name like
       `Site('commons')`, `Site('meta')` or `Site('wikidata')`.
    .. versionchanged:: 10.0
       *url* does not have to contain an api, requests or script path
       any longer.

    :param code: language code (override config.mylang)
        code may also be a sitename like 'wikipedia:test'
    :param fam: family name or object (override config.family)
    :param user: bot user name to use on this site (override config.usernames)
    :param interface: site class or name of class in :py:obj:`pywikibot.site`
        (override config.site_interface)
    :param url: Instead of code and fam, does try to get a Site based on the
        URL. Still requires that the family supporting that URL exists.
    :raises ValueError: URL and pair of code and family given
    :raises ValueError: Invalid interface name
    :raises ValueError: Missing Site code
    :raises ValueError: Missing Site family
    """
    if url:
        # Either code and fam or url with optional fam for AutoFamily name
        if code:
            raise ValueError(
                'URL to the wiki OR a pair of code and family name '
                'should be provided')
        code, fam = _code_fam_from_url(url, fam)
    elif code and ':' in code:
        if fam:
            raise ValueError(
                'sitename OR a pair of code and family name '
                'should be provided')
        fam, _, code = code.partition(':')
    else:
        if not fam:  # try code as family
            with suppress(exceptions.UnknownFamilyError):
                fam = Family.load(code)
        # Fallback to config defaults
        code = code or _config.mylang
        fam = fam or _config.family

    if not (code and fam):
        raise ValueError(f"Missing Site {'code' if not code else 'family'}")

    if not isinstance(fam, Family):
        fam = Family.load(fam)

    fam = cast(Family, fam)
    interface = interface or fam.interface(code)

    # config.usernames is initialised with a defaultdict for each family name
    family_name = str(fam)

    code_to_user = {}
    if '*' in _config.usernames:  # T253127: usernames is a defaultdict
        code_to_user = _config.usernames['*'].copy()
    code_to_user.update(_config.usernames[family_name])
    user = user or code_to_user.get(code) or code_to_user.get('*')

    if not isinstance(interface, type):
        # If it isn't a class, assume it is a string
        interface = cast(str, interface)
        try:
            tmp = __import__('pywikibot.site', fromlist=[interface])
        except ImportError:
            raise ValueError(f'Invalid interface name: {interface}')

        interface = getattr(tmp, interface)

    if not issubclass(interface, _BaseSite):
        warning(f'Site called with interface={interface.__name__}')

    user = normalize_username(user)
    key = f'{interface.__name__}:{fam}:{code}:{user}'
    if key not in _sites or not isinstance(_sites[key], interface):
        _sites[key] = interface(code=code, fam=fam, user=user)
        debug(f"Instantiated {interface.__name__} object '{_sites[key]}'")

        if _sites[key].code != code:
            warnings.warn(f'Site {_sites[key]} instantiated using different '
                          f'code "{code}"', UserWarning, 2)

    return _sites[key]


# These imports depend on Wb* classes above.
from pywikibot.page import (  # noqa: E402
    Category,
    Claim,
    FilePage,
    ItemPage,
    LexemeForm,
    LexemePage,
    LexemeSense,
    Link,
    MediaInfo,
    Page,
    PropertyPage,
    SiteLink,
    User,
    html2unicode,
)


def showDiff(oldtext: str,  # noqa: N802
             newtext: str,
             context: int = 0) -> None:
    """Output a string showing the differences between oldtext and newtext.

    The differences are highlighted (only on compatible systems) to show which
    changes were made.
    """
    PatchManager(oldtext, newtext, context=context).print_hunks()


# Throttle and thread handling


def sleep(secs: int) -> None:
    """Suspend execution of the current thread for the given number of seconds.

    Drop this process from the throttle log if wait time is greater than
    30 seconds by calling :func:`stopme`.
    """
    if secs >= 30:
        stopme()
    time_sleep(secs)


def stopme() -> None:
    """Drop this process from the throttle log, after pending threads finish.

    Can be called manually if desired but usually it is not necessary.
    Does not clean :func:`async_manager`. This should be run when a bot
    does not interact with the Wiki, or when it has stopped doing so.
    After a bot has run ``stopme()`` it will not slow down other bots
    instances any more.

    ``stopme()`` is called with :func:`sleep` function during long
    delays and with :meth:`bot.BaseBot.exit` to wait for pending write
    threads.
    """
    _flush(False)


def _flush(stop: bool = True) -> None:
    """Drop this process from the throttle log, after pending threads finish.

    Wait for the page-putter to flush its queue. Also drop this process
    from the throttle log. Called automatically at Python exit.

    :param stop: Also clear :func:`async_manager`s put queue. This is
        only done at exit time.
    """
    debug('_flush() called')

    def remaining() -> tuple[int, datetime.timedelta]:
        remaining_pages = page_put_queue.qsize()
        if stop:
            # -1 because we added a None element to stop the queue
            remaining_pages -= 1

        remaining_seconds = datetime.timedelta(
            seconds=round(remaining_pages * _config.put_throttle))
        return (remaining_pages, remaining_seconds)

    if stop:
        # None task element leaves async_manager
        page_put_queue.put((None, [], {}))

    num, sec = remaining()
    if num > 0 and sec.total_seconds() > _config.noisysleep:
        output(f'<<lightblue>>Waiting for {num} pages to be put. '
               f'Estimated time remaining: {sec}')

    exit_queue = None
    if _putthread is not threading.current_thread():
        while _putthread.is_alive() and not (page_put_queue.empty()
                                             and page_put_queue_busy.empty()):
            try:
                _putthread.join(1)
            except KeyboardInterrupt:
                exit_queue = input_yn(
                    'There are {} pages remaining in the queue. Estimated '
                    'time remaining: {}\nReally exit?'.format(*remaining()),
                    default=False, automatic_quit=False)
                break

    if exit_queue is False:
        # handle the queue when _putthread is stopped after KeyboardInterrupt
        with suppress(KeyboardInterrupt):
            async_manager(block=False)

    if not stop:
        # delete the put queue
        with page_put_queue.mutex:
            page_put_queue.all_tasks_done.notify_all()
            page_put_queue.queue.clear()
            page_put_queue.not_full.notify_all()

    # only need one drop() call because all throttles use the same global pid
    with suppress(KeyError):
        _sites.popitem()[1].throttle.drop()
        log('Dropped throttle(s).')


# Create a separate thread for asynchronous page saves (and other requests)
def async_manager(block=True) -> None:
    """Daemon to take requests from the queue and execute them in background.

    :param block: If true, block :attr:`page_put_queue` if necessary
        until a request is available to process. Otherwise process a
        request if one is immediately available, else leave the function.
    """
    while True:
        if not block and page_put_queue.empty():
            break
        (request, args, kwargs) = page_put_queue.get(block)
        page_put_queue_busy.put(None)
        if request is None:
            break
        request(*args, **kwargs)
        page_put_queue.task_done()
        page_put_queue_busy.get()


def async_request(request: Callable, *args: Any, **kwargs: Any) -> None:
    """Put a request on the queue, and start the daemon if necessary."""
    if not _putthread.is_alive():
        with page_put_queue.mutex, suppress(AssertionError, RuntimeError):
            _putthread.start()
    page_put_queue.put((request, args, kwargs))


#: Queue to hold pending requests
page_put_queue: Queue = Queue(_config.max_queue_size)

# queue to signal that async_manager is working on a request. See T147178.
page_put_queue_busy: Queue = Queue(_config.max_queue_size)
# set up the background thread
_putthread = threading.Thread(target=async_manager,
                              name='Put-Thread',  # for debugging purposes
                              daemon=True)
atexit.register(_flush)
