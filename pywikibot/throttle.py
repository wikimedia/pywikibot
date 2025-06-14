"""Mechanics to slow down wiki read and/or write rate."""
#
# (C) Pywikibot team, 2008-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import itertools
import math
import threading
import time
from collections import Counter
from contextlib import suppress
from hashlib import blake2b
from typing import NamedTuple

import pywikibot
from pywikibot import config
from pywikibot.backports import Counter as CounterType
from pywikibot.tools import deprecated


FORMAT_LINE = '{module_id} {pid} {time} {site}\n'

pid: bool | int = False
"""Global process identifier.

When the first Throttle is instantiated, it will set this variable to a
positive integer, which will apply to all throttle objects created by
this process.
"""


class ProcEntry(NamedTuple):

    """ProcEntry namedtuple."""

    module_id: str
    pid: int
    time: int
    site: str


class Throttle:

    """Control rate of access to wiki server.

    Calling this object blocks the calling thread until at least
    `'delay'` seconds have passed since the previous call.

    Each Site initiates one Throttle object (`site.throttle`) to control
    the rate of access.

    :param site: site or sitename for this Throttle. If site is an empty
        string, it will not be written to the throttle.ctrl file.
    :param mindelay: The minimal delay, also used for read access
    :param maxdelay: The maximal delay
    :param writedelay: The write delay
    """

    # Check throttle file again after this many seconds:
    checkdelay: int = 300
    # The number of seconds entries of a process need to be counted
    expiry: int = 600

    def __init__(self, site: pywikibot.site.BaseSite | str, *,
                 mindelay: int | None = None,
                 maxdelay: int | None = None,
                 writedelay: int | float | None = None) -> None:
        """Initializer."""
        self.lock = threading.RLock()
        self.lock_write = threading.RLock()
        self.lock_read = threading.RLock()
        self.mysite = str(site)
        self.ctrlfilename = config.datafilepath('throttle.ctrl')
        self.mindelay = mindelay or config.minthrottle
        self.maxdelay = maxdelay or config.maxthrottle
        self.writedelay = writedelay or config.put_throttle
        self.last_read = 0.0
        self.last_write = 0.0
        self.next_multiplicity = 1.0

        self.retry_after = 0  # set by http.request
        self.delay = 0
        self.checktime = 0.0
        self.modules: CounterType[str] = Counter()

        self.checkMultiplicity()
        self.setDelays()

    @property
    @deprecated('expiry', since='8.4.0')
    def dropdelay(self):
        """Ignore processes that have not made a check in this many seconds.

        .. deprecated:: 8.4
           use *expiry* instead.
        """
        return self.expiry

    @property
    @deprecated('expiry', since='8.4.0')
    def releasepid(self):
        """Free the process id after this many seconds.

        .. deprecated:: 8.4
           use *expiry* instead.
        """
        return self.expiry

    @staticmethod
    def _module_hash(module=None) -> str:
        """Convert called module name to a hash."""
        if module is None:
            module = pywikibot.calledModuleName()
        module = module.encode()
        hashobj = blake2b(module, digest_size=2)
        return hashobj.hexdigest()

    def _read_file(self, raise_exc: bool = False):
        """Yield process entries from file."""
        try:
            with open(self.ctrlfilename) as f:
                lines = f.readlines()
        except OSError:
            if raise_exc and pid:
                raise
            return

        for line in lines:
            # parse line; format is "module_id pid timestamp site"
            try:
                _id, _pid, _time, _site = line.split(' ')
                proc_entry = ProcEntry(
                    module_id=_id,
                    pid=int(_pid),
                    time=int(float(_time)),
                    site=_site.rstrip()
                )
            except (IndexError, ValueError):  # pragma: no cover
                # Sometimes the file gets corrupted ignore that line
                continue
            yield proc_entry

    def _write_file(self, processes) -> None:
        """Write process entries to file."""
        if not isinstance(processes, list):
            processes = list(processes)
        processes.sort(key=lambda p: (p.pid, p.site))

        with suppress(IOError), open(self.ctrlfilename, 'w') as f:
            for p in processes:
                f.write(FORMAT_LINE.format_map(p._asdict()))

    def checkMultiplicity(self) -> None:
        """Count running processes for site and set process_multiplicity.

        .. versionchanged:: 7.0
           process is not written to throttle.ctrl file if site is empty.
        """
        global pid
        mysite = self.mysite
        pywikibot.debug(f'Checking multiplicity: pid = {pid}')
        with self.lock:
            processes = []
            used_pids = set()
            count = 1

            now = time.time()
            for proc in self._read_file(raise_exc=True):
                used_pids.add(proc.pid)
                if now - proc.time > self.expiry:
                    continue  # process has expired, drop from file

                if proc.site == mysite and proc.pid != pid:
                    count += 1

                if proc.site != mysite or proc.pid != pid:
                    processes.append(proc)

            free_pid = (i for i in itertools.count(start=1)
                        if i not in used_pids)
            if not pid:
                pid = next(free_pid)

            self.checktime = time.time()
            processes.append(
                ProcEntry(module_id=self._module_hash(), pid=pid,
                          time=self.checktime, site=mysite))
            self.modules = Counter(p.module_id for p in processes)

            if not mysite:
                del processes[-1]

            self._write_file(sorted(processes, key=lambda p: p.pid))

            self.process_multiplicity = count
            pywikibot.log(f'Found {count} {mysite} processes running,'
                          ' including this one.')

    def setDelays(
        self,
        delay=None,
        writedelay=None,
        absolute: bool = False
    ) -> None:
        """Set the nominal delays in seconds.

        Defaults to config values.
        """
        with self.lock:
            delay = delay or self.mindelay
            writedelay = writedelay or config.put_throttle
            if absolute:
                self.maxdelay = delay
                self.mindelay = delay
            self.delay = delay
            self.writedelay = min(max(self.mindelay, writedelay),
                                  self.maxdelay)
            # Start the delay count now, not at the next check
            self.last_read = self.last_write = time.time()

    def getDelay(self, write: bool = False):
        """Return the actual delay, accounting for multiple processes.

        This value is the maximum wait between reads/writes, not taking
        into account of how much time has elapsed since the last access.
        """
        thisdelay = self.writedelay if write else self.delay

        # We're checking for multiple processes
        if time.time() > self.checktime + self.checkdelay:
            self.checkMultiplicity()
        multiplied_delay = self.mindelay * self.next_multiplicity
        if thisdelay < multiplied_delay:
            thisdelay = multiplied_delay
        elif thisdelay > self.maxdelay:
            thisdelay = self.maxdelay
        thisdelay *= self.process_multiplicity
        return thisdelay

    def waittime(self, write: bool = False):
        """Return waiting time in seconds.

        The result is for a query that would be made right now.
        """
        # Take the previous requestsize in account calculating the desired
        # delay this time
        thisdelay = self.getDelay(write=write)
        now = time.time()
        ago = now - (self.last_write if write else self.last_read)
        return max(0.0, thisdelay - ago)

    def drop(self) -> None:
        """Remove me from the list of running bot processes."""
        # drop all throttles with this process's pid, regardless of site
        self.checktime = 0

        now = time.time()
        processes = [p for p in self._read_file()
                     if now - p.time <= self.expiry and p.pid != pid]

        self._write_file(processes)

    @staticmethod
    def wait(seconds: int | float) -> None:
        """Wait for seconds seconds.

        Announce the delay if it exceeds a preset limit.
        """
        if seconds <= 0:
            return

        message = 'Sleeping for {seconds:.1f} seconds, {now}' \
                  .format_map({
                      'seconds': seconds,
                      'now': time.strftime('%Y-%m-%d %H:%M:%S',
                                           time.localtime())})
        if seconds > config.noisysleep:
            pywikibot.info(message)
        else:
            pywikibot.log(message)

        time.sleep(seconds)

    def __call__(self, requestsize: int = 1, write: bool = False) -> None:
        """Block the calling program if the throttle time has not expired.

        Parameter requestsize is the number of Pages to be read/written;
        multiply delay time by an appropriate factor.

        Because this seizes the throttle lock, it will prevent any other
        thread from writing to the same site until the wait expires.
        """
        lock = self.lock_write if write else self.lock_read
        with lock:
            wait = self.waittime(write=write)
            # Calculate the multiplicity of the next delay based on how
            # big the request is that is being posted now.
            # We want to add "one delay" for each factor of two in the
            # size of the request. Getting 64 pages at once allows 6 times
            # the delay time for the server.
            self.next_multiplicity = math.log(1 + requestsize) / math.log(2.0)

            self.wait(wait)

            if write:
                self.last_write = time.time()
            else:
                self.last_read = time.time()

    def lag(self, lagtime: float | None = None) -> None:
        """Seize the throttle lock due to server lag.

        Usually the `self.retry-after` value from `response_header` of the
        last request if available which will be used for wait time.
        Otherwise `lagtime` from api `maxlag` is used. If neither
        `self.retry_after` nor `lagtime` is set, fallback to
        `config.retry_wait`.

        If the `lagtime` is disproportionately high compared to
        `self.retry_after` value, the wait time will be increased.

        This method is used by `api.request`. It will prevent any thread
        from accessing this site.

        :param lagtime: The time to wait for the next request which is
            the last `maxlag` time from api warning. This is only used
            as a fallback if `self.retry_after` isn't set.
        """
        started = time.time()
        with self.lock:
            waittime = lagtime or config.retry_wait
            if self.retry_after:
                waittime = max(self.retry_after, waittime / 5)
            # wait not more than retry_max seconds
            delay = min(waittime, config.retry_max)
            # account for any time we waited while acquiring the lock
            wait = delay - (time.time() - started)
            self.wait(wait)

    def get_pid(self, module: str) -> int:
        """Get the global pid if the module is running multiple times."""
        return pid if self.modules[self._module_hash(module)] > 1 else 0
