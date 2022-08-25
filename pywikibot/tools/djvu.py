"""Wrapper around djvulibre to access djvu files properties and content."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
import os
import re
import subprocess
from collections import Counter

import pywikibot


def _call_cmd(args, lib: str = 'djvulibre') -> tuple:
    """
    Tiny wrapper around subprocess.Popen().

    :param args: same as Popen()
    :type args: str or typing.Sequence[string]
    :param lib: library to be logged in logging messages
    :return: returns a tuple (res, stdoutdata), where
        res is True if dp.returncode != 0 else False
    """
    if not isinstance(args, str):
        # upcast any param in sequence args to str
        cmd = ' '.join(str(a) for a in args)
    else:
        cmd = args

    dp = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdoutdata, stderrdata = dp.communicate()

    if dp.returncode != 0:
        pywikibot.error('{} error; {}'.format(lib, cmd))
        pywikibot.error(str(stderrdata))
        return (False, stdoutdata)

    pywikibot.log('SUCCESS: {} (PID: {})'.format(cmd, dp.pid))

    return (True, stdoutdata)


class DjVuFile:

    """Wrapper around djvulibre to access djvu files properties and content.

    Perform file existence checks.

    Control characters in djvu text-layer are converted for convenience
    (see http://djvu.sourceforge.net/doc/man/djvused.html for control chars
    details).

    """

    def __init__(self, file: str) -> None:
        """
        Initializer.

        :param file: filename (including path) to djvu file
        """
        self._filename = file
        filename = os.path.expanduser(file)
        filename = os.path.abspath(filename)
        # Check file exists and has read permissions.
        with open(filename):
            self.file = filename
        self.dirname = os.path.dirname(filename)

        # pattern for parsing of djvudump output.
        self._pat_form = re.compile(
            r' *?FORM:DJVU *?\[\d+\] *?(?P<id>{[^\}]*?})? *?\[P(?P<n>\d+)\]')
        self._pat_info = re.compile(
            r'DjVu.*?(?P<size>\d+x\d+).*?(?P<dpi>\d+) dpi')

    def __repr__(self) -> str:
        """Return a more complete string representation."""
        return "{}.{}('{}')".format(self.__module__,
                                    self.__class__.__name__,
                                    self._filename)

    def __str__(self) -> str:
        """Return a string representation."""
        return "{}('{}')".format(self.__class__.__name__, self._filename)

    def check_cache(fn):
        """Decorator to check if cache shall be cleared."""
        cache = ['_page_count', '_has_text', '_page_info']

        def wrapper(obj, *args, **kwargs):
            force = kwargs.get('force', False)
            if force:
                for el in cache:
                    obj.__dict__.pop(el, None)
            _res = fn(obj, *args, **kwargs)
            return _res
        return wrapper

    def check_page_number(fn):
        """Decorator to check if page number is valid.

        :raises ValueError
        """
        def wrapper(obj, *args, **kwargs):
            n = args[0]
            force = kwargs.get('force', False)
            if not 1 <= n <= obj.number_of_images(force=force):
                raise ValueError('Page {} not in file {} [{}-{}]'
                                 .format(int(n), obj.file, int(n),
                                         int(obj.number_of_images())))
            _res = fn(obj, *args, **kwargs)
            return _res
        return wrapper

    @check_cache
    def number_of_images(self, force: bool = False):
        """
        Return the number of images in the djvu file.

        :param force: if True, refresh the cached data
        """
        if not hasattr(self, '_page_count'):
            res, stdoutdata = _call_cmd(['djvused', '-e', 'n', self.file])
            if not res:
                return False
            self._page_count = int(stdoutdata)
        return self._page_count

    @check_page_number
    def page_info(self, n: int, force: bool = False):
        """
        Return a tuple (id, (size, dpi)) for page n of djvu file.

        :param n: page n of djvu file
        :param force: if True, refresh the cached data
        """
        if not hasattr(self, '_page_info') or force:
            self._get_page_info(force=force)
        return self._page_info[n]

    @check_cache
    def _get_page_info(self, force: bool = False):
        """
        Return a dict of tuples (id, (size, dpi)) for all pages of djvu file.

        :param force: if True, refresh the cached data
        """
        if not hasattr(self, '_page_info'):
            self._page_info = {}

            res, stdoutdata = _call_cmd(['djvudump', self.file])
            if not res:
                return False

            has_text = False
            for line in stdoutdata.decode('utf-8').split('\n'):
                if 'TXTz' in line:
                    has_text = True

                if 'FORM:DJVU' in line:
                    m = self._pat_form.search(line)
                    if m:
                        key, id = int(m.group('n')), m.group('id')
                    else:
                        # If djvu doc has only one page,
                        # FORM:DJVU line in djvudump has no id
                        key, id = 1, ''

                if 'INFO' in line:
                    m = self._pat_info.search(line)
                    if m:
                        size, dpi = m.group('size'), int(m.group('dpi'))
                    else:
                        size, dpi = None, None
                else:
                    continue

                self._page_info[key] = (id, (size, dpi))
            self._has_text = has_text
        return self._page_info

    def get_most_common_info(self):
        """Return most common size and dpi for pages in djvu file."""
        cnt = Counter(s_d for _, s_d in self._get_page_info().values())
        (size, dpi), _ = cnt.most_common()[0]
        return size, dpi

    @check_cache
    def has_text(self, force: bool = False):
        """
        Test if the djvu file has a text-layer.

        :param force: if True, refresh the cached data
        """
        if not hasattr(self, '_has_text'):
            self._get_page_info(force=force)
        return self._has_text

    @staticmethod
    def _remove_control_chars(data):
        """Remove djvu format control characters.

        See http://djvu.sourceforge.net/doc/man/djvused.html for control chars.

        :param data: the data checked for djvu format control characters
        """
        txt = data.decode('utf-8')
        # vertical tab (\013=\x0b): remove
        txt = txt.replace('\x0b', '')
        # group (\035=\x1d) separator: replace with \n
        txt = txt.replace('\x1d', '\n')
        # unit separator (\037=\x1f): replace with \n
        txt = txt.replace('\x1f', '\n')
        # feed char (\f=\x0c), \n and trailing spaces: strip
        txt = txt.strip('\x0c\n ')
        return txt

    @check_page_number
    @check_cache
    def get_page(self, n: int, force: bool = False):
        """
        Get page n for djvu file.

        :param n: page n of djvu file
        :param force: if True, refresh the cached data
        """
        if not self.has_text(force=force):
            raise ValueError('Djvu file {} has no text layer.'
                             .format(self.file))
        res, stdoutdata = _call_cmd(['djvutxt', '--page={}'.format(int(n)),
                                     self.file])
        if not res:
            return False
        return self._remove_control_chars(stdoutdata)

    @check_page_number
    def whiten_page(self, n) -> bool:
        """Replace page 'n' of djvu file with a blank page.

        :param n: page n of djvu file
        :type n: int
        """
        # tmp files for creation/insertion of a white page.
        white_ppm = os.path.join(self.dirname, 'white_page.ppm')
        white_djvu = os.path.join(self.dirname, 'white_page.djvu')

        n_tot = self.number_of_images()

        # Check n is in valid range and set ref_page number for final checks.
        ref_page = 2 if n == 1 else n - 1

        size, dpi = self.get_most_common_info()

        # Generate white_page.
        res, _ = _call_cmd(['convert', '-size', size, 'xc:white', white_ppm],
                           lib='ImageMagik')
        if not res:
            return False

        # Convert white_page to djvu.
        res, data = _call_cmd(['c44', white_ppm, '-dpi', dpi])
        os.unlink(white_ppm)  # rm white_page.ppm before returning.
        if not res:
            return False

        # Delete page n.
        # Get ref page info for later checks.
        info_ref_page = self.page_info(ref_page)
        res, data = _call_cmd(['djvm', '-d', self.file, n])
        if not res:
            return False

        # Insert new page
        res, data = _call_cmd(['djvm', '-i', self.file, white_djvu, n])
        os.unlink(white_djvu)  # rm white_page.djvu before returning.
        if not res:
            return False

        # Check if page processing is as expected.
        expected_id = '{%s}' % os.path.basename(white_djvu)
        assert self.number_of_images(force=True) == n_tot
        assert self.page_info(n) == (expected_id, (size, dpi))  # white page id
        assert self.page_info(ref_page) == info_ref_page  # ref page info.

        return True

    @check_page_number
    def delete_page(self, n) -> bool:
        """Delete page 'n' of djvu file.

        :param n: page n of djvu file
        :type n: int
        """
        n_tot = self.number_of_images()

        # Check n is in valid range and set ref_page number for final checks.
        ref_page = n - 1 if n == n_tot else n + 1
        new_ref_page = n - 1 if n == n_tot else n

        # Delete page n.
        # Get ref page info for later checks.
        info_ref_page = self.page_info(ref_page)
        res, _ = _call_cmd(['djvm', '-d', self.file, n])
        if not res:
            return False

        # Check if page processing is as expected.
        # ref page info.
        if n_tot > 2:
            assert self.number_of_images(force=True) == n_tot - 1
            # cache cleared above
            assert self.page_info(new_ref_page) == info_ref_page
        else:
            # If djvu has only one page, FORM:DJVU line in djvudump has no id
            _id, (sz, dpi) = info_ref_page
            assert self.page_info(new_ref_page, force=True) == ('', (sz, dpi))

        return True

    # This is to be used only if this class is subclassed and the decorators
    # needs to be used by the child.
    check_page_number = staticmethod(check_page_number)
    check_cache = staticmethod(check_cache)
