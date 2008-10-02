# -*- coding: utf-8  -*-
"""
Mechanics to slow down wiki read and/or write rate.
"""
#
# (C) Pywikipedia bot team, 2008
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: $'

import config
import pywikibot

import logging
import math
import threading
import time

logger = logging.getLogger("wiki")

pid = False   # global process identifier
              # Don't check for other processes unless this is set


class Throttle(object):
    """Control rate of access to wiki server

    Calling this object blocks the calling thread until at least 'delay'
    seconds have passed since the previous call.

    Each Site initiates one Throttle object (site.throttle) to control the
    rate of access.

    """
    def __init__(self, site, mindelay=config.minthrottle,
                       maxdelay=config.maxthrottle,
                       writedelay=config.put_throttle,
                       multiplydelay=True, verbosedelay=False):
        self.lock = threading.RLock()
        self.mysite = str(site)
        self.logfn = config.datafilepath('throttle.log')
        self.mindelay = mindelay
        self.maxdelay = maxdelay
        self.writedelay = writedelay
        self.last_read = 0
        self.last_write = 0
        self.next_multiplicity = 1.0
        self.checkdelay = 300  # Check logfile again after this many seconds
        self.dropdelay = 750   # Ignore processes that have not made
                               # a check in this many seconds
        self.releasepid = 1800 # Free the process id after this many seconds
        self.lastwait = 0.0
        self.delay = 0
        self.verbosedelay = verbosedelay
        if multiplydelay:
            self.checkMultiplicity()
        self.setDelays()

    def checkMultiplicity(self):
        global pid
        self.lock.acquire()
        logger.debug("Checking multiplicity: pid = %(pid)s" % globals())
        try:
            processes = []
            my_pid = 1
            count = 1
            try:
                f = open(self.logfn, 'r')
            except IOError:
                if not pid:
                    pass
                else:
                    raise
            else:
                now = time.time()
                for line in f.readlines():
                    try:
                        line = line.split(' ')
                        this_pid = int(line[0])
                        ptime = int(line[1].split('.')[0])
                        this_site = line[2].rstrip()
                    except (IndexError, ValueError):
                        continue    # Sometimes the file gets corrupted
                                    # ignore that line
                    if now - ptime > self.releasepid:
                        continue    # process has expired, drop from file
                    if now - ptime <= self.dropdelay \
                            and this_site == self.mysite \
                            and this_pid != pid:
                        count += 1
                    if this_site != self.mysite or this_pid != pid:
                        processes.append({'pid': this_pid,
                                          'time': ptime,
                                          'site': this_site})
                    if not pid and this_pid >= my_pid:
                        my_pid = this_pid+1

            if not pid:
                pid = my_pid
            self.checktime = time.time()
            processes.append({'pid': my_pid,
                              'time': self.checktime,
                              'site': self.mysite})
            f = open(self.logfn, 'w')
            processes.sort(key=lambda p:(p['pid'], p['site']))
            for p in processes:
                f.write("%(pid)s %(time)s %(site)s\n" % p)
            f.close()
            self.process_multiplicity = count
            if self.verbosedelay:
                logger.info(
u"Found %(count)s processes running, including the current process."
                    % locals())
        finally:
            self.lock.release()

    def setDelays(self, delay=None, writedelay=None, absolute=False):
        """Set the nominal delays in seconds. Defaults to config values."""
        self.lock.acquire()
        try:
            if delay is None:
                delay = self.mindelay
            if writedelay is None:
                writedelay = self.writedelay
            if absolute:
                self.maxdelay = delay
                self.mindelay = delay
            self.delay = delay
            self.writedelay = min(max(self.mindelay, writedelay),
                                  self.maxdelay)
            # Start the delay count now, not at the next check
            self.last_read = self.last_write = time.time()
        finally:
            self.lock.release()

    def getDelay(self, write=False):
        """Return the actual delay, accounting for multiple processes.

        This value is the maximum wait between reads/writes, not taking
        account of how much time has elapsed since the last access.

        """
        global pid
        if write:
            thisdelay = self.writedelay
        else:
            thisdelay = self.delay
        if pid: # If set, we're checking for multiple processes
            if time.time() > self.checktime + self.checkdelay:
                self.checkMultiplicity()
            if thisdelay < (self.mindelay * self.next_multiplicity):
                thisdelay = self.mindelay * self.next_multiplicity
            elif thisdelay > self.maxdelay:
                thisdelay = self.maxdelay
            thisdelay *= self.process_multiplicity
        return thisdelay

    def waittime(self, write=False):
        """Return waiting time in seconds if a query would be made right now"""
        # Take the previous requestsize in account calculating the desired
        # delay this time
        thisdelay = self.getDelay(write=write)
        now = time.time()
        if write:
            ago = now - self.last_write
        else:
            ago = now - self.last_read
        if ago < thisdelay:
            delta = thisdelay - ago
            return delta
        else:
            return 0.0

    def drop(self):
        """Remove me from the list of running bots processes."""
        self.checktime = 0
        processes = []
        try:
            f = open(self.logfn, 'r')
        except IOError:
            return
        else:
            now = time.time()
            for line in f.readlines():
                try:
                    line = line.split(' ')
                    this_pid = int(line[0])
                    ptime = int(line[1].split('.')[0])
                    this_site = line[2].rstrip()
                except (IndexError,ValueError):
                    continue    # Sometimes the file gets corrupted
                                # ignore that line
                if now - ptime <= self.releasepid \
                        and this_pid != pid:
                    processes.append({'pid': this_pid,
                                      'time': ptime,
                                      'site': this_site})
        f = open(self.logfn, 'w')
        processes.sort(key=lambda p:p['pid'])
        for p in processes:
            f.write("%(pid)s %(time)s %(site)s\n" % p)
        f.close()

    def __call__(self, requestsize=1, write=False):
        """
        Block the calling program if the throttle time has not expired.

        Parameter requestsize is the number of Pages to be read/written;
        multiply delay time by an appropriate factor.

        Because this seizes the throttle lock, it will prevent any other
        thread from writing to the same site until the wait expires.

        """
        self.lock.acquire()
        try:
            wait = self.waittime(write=write)
            # Calculate the multiplicity of the next delay based on how
            # big the request is that is being posted now.
            # We want to add "one delay" for each factor of two in the
            # size of the request. Getting 64 pages at once allows 6 times
            # the delay time for the server.
            self.next_multiplicity = math.log(1+requestsize)/math.log(2.0)
            # Announce the delay if it exceeds a preset limit
            if wait > config.noisysleep:
                logger.info(u"Sleeping for %(wait).1f seconds, %(now)s"
                              % {'wait': wait,
                                 'now': time.strftime("%Y-%m-%d %H:%M:%S",
                                                      time.localtime())
                                } )
            time.sleep(wait)
            if write:
                self.last_write = time.time()
            else:
                self.last_read = time.time()
        finally:
            self.lock.release()

    def lag(self, lagtime):
        """
        Seize the throttle lock due to server lag.

        This will prevent any thread from accessing this site.

        """
        started = time.time()
        self.lock.acquire()
        try:
            # start at 1/2 the current server lag time
            # wait at least 5 seconds but not more than 120 seconds
            delay = min(max(5, lagtime//2), 120)
            # account for any time we waited while acquiring the lock
            wait = delay - (time.time() - started)
            if wait > 0:
                if wait > config.noisysleep:
                    logger.info(u"Sleeping for %(wait).1f seconds, %(now)s"
                                  % {'wait': wait,
                                     'now': time.strftime("%Y-%m-%d %H:%M:%S",
                                                          time.localtime())
                                    } )
                time.sleep(wait)
        finally:
            self.lock.release()

