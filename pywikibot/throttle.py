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

pid = False   # global process identifier
              # Don't check for other processes unless this is set


class Throttle(object):
    """Control rate of access to wiki server

    Calling this object blocks the calling thread until at least 'delay'
    seconds have passed since the previous call.

    Each Site initiates two Throttle objects: get_throttle to control
    the rate of read access, and put_throttle to control the rate of write
    access. These are available as the Site.get_throttle and Site.put_throttle
    objects.

    """
    def __init__(self, site, mindelay=config.minthrottle,
                       maxdelay=config.maxthrottle,
                       multiplydelay=True):
        self.lock = threading.RLock()
        self.mysite = str(site)
        self.mindelay = mindelay
        self.maxdelay = maxdelay
        self.now = 0
        self.next_multiplicity = 1.0
        self.checkdelay = 240  # Check logfile again after this many seconds
        self.dropdelay = 360   # Ignore processes that have not made
                               # a check in this many seconds
        self.releasepid = 1800 # Free the process id after this many seconds
        self.lastwait = 0.0
        self.delay = 0
        if multiplydelay:
            self.checkMultiplicity()
        self.setDelay(mindelay)

    def logfn(self):
        return config.datafilepath('throttle.log')

    def checkMultiplicity(self):
        global pid
        self.lock.acquire()
        logging.debug("Checking multiplicity: pid = %s" % pid)
        try:
            processes = []
            my_pid = 1
            count = 1
            try:
                f = open(self.logfn(), 'r')
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
                    print line,
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
            f = open(self.logfn(), 'w')
            processes.sort(key=lambda p:(p['pid'], p['site']))
            for p in processes:
                f.write("%(pid)s %(time)s %(site)s\n" % p)
            f.close()
            self.process_multiplicity = count
            pywikibot.output(
                u"Found %s processes running, including the current process."
                % count)
        finally:
            self.lock.release()

    def setDelay(self, delay=config.minthrottle, absolute=False):
        """Set the nominal delay in seconds."""
        self.lock.acquire()
        try:
            if absolute:
                self.maxdelay = delay
                self.mindelay = delay
            self.delay = delay
            # Start the delay count now, not at the next check
            self.now = time.time()
        finally:
            self.lock.release()

    def getDelay(self):
        """Return the actual delay, accounting for multiple processes.

        This value is the maximum wait between reads/writes, not taking
        account of how much time has elapsed since the last access.

        """
        global pid
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

    def waittime(self):
        """Return waiting time in seconds if a query would be made right now"""
        # Take the previous requestsize in account calculating the desired
        # delay this time
        thisdelay = self.getDelay()
        now = time.time()
        ago = now - self.now
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
            f = open(self.logfn(), 'r')
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
        f = open(self.logfn(), 'w')
        processes.sort(key=lambda p:p['pid'])
        for p in processes:
            f.write("%(pid)s %(time)s %(site)s\n" % p)
        f.close()

    def __call__(self, requestsize=1):
        """
        Block the calling program if the throttle time has not expired.

        Parameter requestsize is the number of Pages to be read/written;
        multiply delay time by an appropriate factor.
        """
        self.lock.acquire()
        try:
            waittime = self.waittime()
            # Calculate the multiplicity of the next delay based on how
            # big the request is that is being posted now.
            # We want to add "one delay" for each factor of two in the
            # size of the request. Getting 64 pages at once allows 6 times
            # the delay time for the server.
            self.next_multiplicity = math.log(1+requestsize)/math.log(2.0)
            # Announce the delay if it exceeds a preset limit
            if waittime > config.noisysleep:
                pywikibot.output(u"Sleeping for %.1f seconds, %s"
                                 % (waittime,
                                    time.strftime("%Y-%m-%d %H:%M:%S",
                                                  time.localtime()))
                                 )
            time.sleep(waittime)
            self.now = time.time()
        finally:
            self.lock.release()

