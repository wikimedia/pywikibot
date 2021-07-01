#!/usr/bin/python
"""Test tools package alone which don't fit into other tests."""
#
# (C) Pywikibot team, 2015-2021
#
# Distributed under the terms of the MIT license.
import decimal
import os.path
import subprocess
import tempfile
import unittest
from collections import OrderedDict
from collections.abc import Mapping
from contextlib import suppress
from importlib import import_module

from pywikibot import tools
from pywikibot.tools import (
    classproperty,
    has_module,
    is_ip_address,
    suppress_warnings,
)
from tests import join_xml_data_path, mock
from tests.aspects import TestCase, require_modules


class OpenArchiveTestCase(TestCase):

    """
    Unit test class for tools.

    The tests for open_archive requires that article-pyrus.xml* contain all
    the same content after extraction. The content itself is not important.
    The file article-pyrus.xml_invalid.7z is not a valid 7z file and
    open_archive will fail extracting it using 7za.
    """

    net = False

    @classmethod
    def setUpClass(cls):
        """Define base_file and original_content."""
        super().setUpClass()
        cls.base_file = join_xml_data_path('article-pyrus.xml')
        with open(cls.base_file, 'rb') as f:
            cls.original_content = f.read().replace(b'\r\n', b'\n')

    @staticmethod
    def _get_content(*args, **kwargs):
        """Use open_archive and return content using a with-statement."""
        with tools.open_archive(*args, **kwargs) as f:
            return f.read().replace(b'\r\n', b'\n')

    def test_open_archive_normal(self):
        """Test open_archive with no compression in the standard library."""
        self.assertEqual(
            self._get_content(self.base_file), self.original_content)

    def test_open_archive_bz2(self):
        """Test open_archive with bz2 compressor in the standard library."""
        self.assertEqual(
            self._get_content(self.base_file + '.bz2'), self.original_content)
        self.assertEqual(
            self._get_content(self.base_file + '.bz2', use_extension=False),
            self.original_content)

    @require_modules('bz2file')
    def test_open_archive_with_bz2file(self):
        """Test open_archive when bz2file library."""
        old_bz2 = tools.bz2
        try:
            tools.bz2 = import_module('bz2file')
            self.assertEqual(self._get_content(self.base_file + '.bz2'),
                             self.original_content)
            self.assertEqual(self._get_content(self.base_file + '.bz2',
                                               use_extension=False),
                             self.original_content)
        finally:
            tools.bz2 = old_bz2

    def test_open_archive_without_bz2(self):
        """Test open_archive when bz2 and bz2file are not available."""
        old_bz2 = tools.bz2
        bz2_import_error = ('This is a fake exception message that is '
                            'used when bz2 and bz2file are not importable')
        try:
            tools.bz2 = ImportError(bz2_import_error)
            with self.assertRaisesRegex(
                    ImportError,
                    bz2_import_error):
                self._get_content(self.base_file + '.bz2')
        finally:
            tools.bz2 = old_bz2

    def test_open_archive_gz(self):
        """Test open_archive with gz compressor in the standard library."""
        self.assertEqual(
            self._get_content(self.base_file + '.gz'), self.original_content)

    def test_open_archive_7z(self):
        """Test open_archive with 7za if installed."""
        try:
            subprocess.Popen(['7za'], stdout=subprocess.PIPE).stdout.close()
        except OSError:
            self.skipTest('7za not installed')
        self.assertEqual(
            self._get_content(self.base_file + '.7z'), self.original_content)
        with self.assertRaisesRegex(
                OSError,
                'Unexpected STDERR output from 7za '):
            self._get_content(self.base_file + '_invalid.7z',
                              use_extension=True)

    def test_open_archive_lzma(self):
        """Test open_archive with lzma compressor in the standard library."""
        if isinstance(tools.lzma, ImportError):
            self.skipTest('lzma not importable')
        self.assertEqual(
            self._get_content(self.base_file + '.lzma'), self.original_content)
        # Legacy LZMA container formet has no magic, skipping
        # use_extension=False test here
        self.assertEqual(
            self._get_content(self.base_file + '.xz'), self.original_content)
        self.assertEqual(
            self._get_content(self.base_file + '.xz', use_extension=False),
            self.original_content)

    def test_open_archive_without_lzma(self):
        """Test open_archive when lzma is not available."""
        old_lzma = tools.lzma
        lzma_import_error = ('This is a fake exception message that is '
                             'used when lzma is not importable')
        try:
            tools.lzma = ImportError(lzma_import_error)
            with self.assertRaisesRegex(
                    ImportError,
                    lzma_import_error):
                self._get_content(self.base_file + '.lzma')
            with self.assertRaisesRegex(
                    ImportError,
                    lzma_import_error):
                self._get_content(self.base_file + '.xz')
        finally:
            tools.lzma = old_lzma


class OpenArchiveWriteTestCase(TestCase):

    """Test writing with open_archive."""

    net = False

    @classmethod
    def setUpClass(cls):
        """Define base_file and original_content."""
        super().setUpClass()
        cls.base_file = join_xml_data_path('article-pyrus.xml')
        with open(cls.base_file, 'rb') as f:
            cls.original_content = f.read().replace(b'\r\n', b'\n')

    def _write_content(self, suffix):
        try:
            fh, fn = tempfile.mkstemp(suffix)
            with tools.open_archive(fn, 'wb') as f:
                f.write(self.original_content)
            with tools.open_archive(fn, 'rb') as f:
                self.assertEqual(f.read(), self.original_content)
            with open(fn, 'rb') as f:
                return f.read()
        finally:
            os.close(fh)
            os.remove(fn)

    def test_invalid_modes(self):
        """Test various invalid mode configurations."""
        with self.assertRaisesRegex(
                ValueError,
                'Invalid mode: "ra"'):
            tools.open_archive('/dev/null', 'ra')  # two modes besides
        with self.assertRaisesRegex(
                ValueError,
                'Invalid mode: "rt"'):
            tools.open_archive('/dev/null', 'rt')  # text mode
        with self.assertRaisesRegex(
                ValueError,
                'Invalid mode: "br"'):
            tools.open_archive('/dev/null', 'br')  # binary at front
        with self.assertRaisesRegex(
                ValueError,
                'Magic number detection only when reading'):
            tools.open_archive('/dev/null',  # writing without extension
                               'wb', False)

    def test_binary_mode(self):
        """Test that it uses binary mode."""
        with tools.open_archive(self.base_file, 'r') as f:
            self.assertEqual(f.mode, 'rb')
            self.assertIsInstance(f.read(), bytes)

    def test_write_archive_bz2(self):
        """Test writing a bz2 archive."""
        content = self._write_content('.bz2')
        with open(self.base_file + '.bz2', 'rb') as f:
            self.assertEqual(content, f.read())

    def test_write_archive_gz(self):
        """Test writing a gz archive."""
        content = self._write_content('.gz')
        self.assertEqual(content[:3], b'\x1F\x8B\x08')

    def test_write_archive_7z(self):
        """Test writing an archive as a 7z archive."""
        with self.assertRaisesRegex(
                NotImplementedError,
                'It is not possible to write a 7z file.'):
            tools.open_archive('/dev/null.7z', mode='wb')

    def test_write_archive_lzma(self):
        """Test writing a lzma archive."""
        if isinstance(tools.lzma, ImportError):
            self.skipTest('lzma not importable')

        content = self._write_content('.lzma')
        with open(self.base_file + '.lzma', 'rb') as f:
            self.assertEqual(content, f.read())

    def test_write_archive_xz(self):
        """Test writing a xz archive."""
        if isinstance(tools.lzma, ImportError):
            self.skipTest('lzma not importable')

        content = self._write_content('.xz')
        self.assertEqual(content[:6], b'\xFD7zXZ\x00')


class MergeUniqueDicts(TestCase):

    """Test merge_unique_dicts."""

    net = False
    dct1 = {'foo': 'bar', '42': 'answer'}
    dct2 = {47: 'Star', 74: 'Trek'}
    dct_both = dct1.copy()
    dct_both.update(dct2)

    def test_single(self):
        """Test that it returns the dict itself when there is only one."""
        self.assertEqual(tools.merge_unique_dicts(self.dct1), self.dct1)
        self.assertEqual(tools.merge_unique_dicts(**self.dct1), self.dct1)

    def test_multiple(self):
        """Test that it actually merges dicts."""
        self.assertEqual(tools.merge_unique_dicts(self.dct1, self.dct2),
                         self.dct_both)
        self.assertEqual(tools.merge_unique_dicts(self.dct2, **self.dct1),
                         self.dct_both)

    def test_different_type(self):
        """Test that the keys can be different types."""
        self.assertEqual(tools.merge_unique_dicts({'1': 'str'}, {1: 'int'}),
                         {'1': 'str', 1: 'int'})

    def test_conflict(self):
        """Test that it detects conflicts."""
        with self.assertRaisesRegex(ValueError, '42'):
            tools.merge_unique_dicts(self.dct1, **{'42': 'bad'})
        with self.assertRaisesRegex(ValueError, '42'):
            tools.merge_unique_dicts(self.dct1, self.dct1)
        with self.assertRaisesRegex(ValueError, '42'):
            tools.merge_unique_dicts(self.dct1, **self.dct1)


class TestIsSliceWithEllipsis(TestCase):

    """Test islice_with_ellipsis."""

    net = False

    it = ['a', 'b', 'c', 'd', 'f']
    it_null = []

    def test_show_default_marker(self):
        """Test marker is shown without kwargs."""
        stop = 2
        it = list(tools.islice_with_ellipsis(self.it, stop))
        self.assertLength(it, stop + 1)  # +1 to consider marker.
        self.assertEqual(it[:-1], self.it[:stop])
        self.assertEqual(it[-1], '…')

    def test_show_custom_marker(self):
        """Test correct marker is shown with kwargs.."""
        stop = 2
        it = list(tools.islice_with_ellipsis(self.it, stop, marker='new'))
        self.assertLength(it, stop + 1)  # +1 to consider marker.
        self.assertEqual(it[:-1], self.it[:stop])
        self.assertNotEqual(it[-1], '…')
        self.assertEqual(it[-1], 'new')

    def test_show_marker_with_start_stop(self):
        """Test marker is shown with start and stop without kwargs."""
        start = 1
        stop = 3
        it = list(tools.islice_with_ellipsis(self.it, start, stop))
        self.assertLength(it, stop - start + 1)  # +1 to consider marker.
        self.assertEqual(it[:-1], self.it[start:stop])
        self.assertEqual(it[-1], '…')

    def test_show_custom_marker_with_start_stop(self):
        """Test marker is shown with start and stop with kwargs."""
        start = 1
        stop = 3
        it = list(tools.islice_with_ellipsis(
            self.it, start, stop, marker='new'))
        self.assertLength(it, stop - start + 1)  # +1 to consider marker.
        self.assertEqual(it[:-1], self.it[start:stop])
        self.assertNotEqual(it[-1], '…')
        self.assertEqual(it[-1], 'new')

    def test_show_marker_with_stop_zero(self):
        """Test marker is shown with stop for non empty iterable."""
        stop = 0
        it = list(tools.islice_with_ellipsis(self.it, stop))
        self.assertLength(it, stop + 1)  # +1 to consider marker.
        self.assertEqual(it[-1], '…')

    def test_do_not_show_marker_with_stop_zero(self):
        """Test marker is shown with stop for empty iterable."""
        stop = 0
        it = list(tools.islice_with_ellipsis(self.it_null, stop))
        self.assertLength(it, stop)

    def test_do_not_show_marker(self):
        """Test marker is not shown when no marker is specified."""
        import itertools
        stop = 2
        it_1 = list(tools.islice_with_ellipsis(self.it, stop, marker=None))
        it_2 = list(itertools.islice(self.it, stop))
        self.assertEqual(it_1, it_2)  # same behavior as islice().

    def test_do_not_show_marker_when_get_all(self):
        """Test marker is not shown when all elements are retrieved."""
        stop = None
        it = list(tools.islice_with_ellipsis(self.it, stop))
        self.assertLength(it, len(self.it))
        self.assertEqual(it, self.it)
        self.assertNotEqual(it[-1], '…')


def passthrough(x):
    """Return x."""
    return x


class SkipList(set):

    """Container that ignores items."""

    skip_list = [1, 3]

    def __contains__(self, item):
        """Override to not process some items."""
        if item in self.skip_list:
            return True

        return super().__contains__(item)


class ProcessAgainList(set):

    """Container that keeps processing certain items."""

    process_again_list = [1, 3]

    def add(self, item):
        """Override to not add some items."""
        if item in self.process_again_list:
            return

        return super().add(item)


class ContainsStopList(set):

    """Container that stops when encountering items."""

    stop_list = []

    def __contains__(self, item):
        """Override to stop on encountering items."""
        if item in self.stop_list:
            raise StopIteration

        return super().__contains__(item)


class AddStopList(set):

    """Container that stops when encountering items."""

    stop_list = []

    def add(self, item):
        """Override to not continue on encountering items."""
        if item in self.stop_list:
            raise StopIteration

        super().add(item)


class TestFilterUnique(TestCase):

    """Test filter_unique."""

    net = False

    ints = [1, 3, 2, 1, 2, 1, 2, 4, 2]
    strs = [str(i) for i in ints]
    decs = [decimal.Decimal(i) for i in ints]

    def _test_dedup_int(self, deduped, deduper, key=None):
        """Test filter_unique results for int."""
        if not key:
            key = passthrough

        self.assertIsEmpty(deduped)

        self.assertEqual(next(deduper), 1)
        self.assertEqual(next(deduper), 3)

        if key in (hash, passthrough):
            if isinstance(deduped, OrderedDict):
                self.assertEqual(list(deduped.keys()), [1, 3])
            elif isinstance(deduped, Mapping):
                self.assertCountEqual(list(deduped.keys()), [1, 3])
            else:
                self.assertEqual(deduped, {1, 3})

        self.assertEqual(next(deduper), 2)
        self.assertEqual(next(deduper), 4)

        if key in (hash, passthrough):
            if isinstance(deduped, OrderedDict):
                self.assertEqual(list(deduped.keys()), [1, 3, 2, 4])
            elif isinstance(deduped, Mapping):
                self.assertCountEqual(list(deduped.keys()), [1, 2, 3, 4])
            else:
                self.assertEqual(deduped, {1, 2, 3, 4})

        with self.assertRaises(StopIteration):
            next(deduper)

    def _test_dedup_str(self, deduped, deduper, key=None):
        """Test filter_unique results for str."""
        if not key:
            key = passthrough

        self.assertIsEmpty(deduped)

        self.assertEqual(next(deduper), '1')
        self.assertEqual(next(deduper), '3')

        if key in (hash, passthrough):
            if isinstance(deduped, Mapping):
                self.assertEqual(deduped.keys(), [key('1'), key('3')])
            else:
                self.assertEqual(deduped, {key('1'), key('3')})

        self.assertEqual(next(deduper), '2')
        self.assertEqual(next(deduper), '4')

        if key in (hash, passthrough):
            if isinstance(deduped, Mapping):
                self.assertEqual(deduped.keys(), [key(i) for i in self.strs])
            else:
                self.assertEqual(deduped, {key(i) for i in self.strs})

        with self.assertRaises(StopIteration):
            next(deduper)

    def test_set(self):
        """Test filter_unique with a set."""
        deduped = set()
        deduper = tools.filter_unique(self.ints, container=deduped)
        self._test_dedup_int(deduped, deduper)

    def test_dict(self):
        """Test filter_unique with a dict."""
        deduped = {}
        deduper = tools.filter_unique(self.ints, container=deduped)
        self._test_dedup_int(deduped, deduper)

    def test_OrderedDict(self):
        """Test filter_unique with an OrderedDict."""
        deduped = OrderedDict()
        deduper = tools.filter_unique(self.ints, container=deduped)
        self._test_dedup_int(deduped, deduper)

    def test_int_hash(self):
        """Test filter_unique with ints using hash as key."""
        deduped = set()
        deduper = tools.filter_unique(self.ints, container=deduped, key=hash)
        self._test_dedup_int(deduped, deduper, hash)

    def test_int_id(self):
        """Test filter_unique with ints using id as key."""
        deduped = set()
        deduper = tools.filter_unique(self.ints, container=deduped, key=id)
        self._test_dedup_int(deduped, deduper, id)

    def test_obj(self):
        """Test filter_unique with objects."""
        deduped = set()
        deduper = tools.filter_unique(self.decs, container=deduped)
        self._test_dedup_int(deduped, deduper)

    def test_obj_hash(self):
        """Test filter_unique with objects using hash as key."""
        deduped = set()
        deduper = tools.filter_unique(self.decs, container=deduped, key=hash)
        self._test_dedup_int(deduped, deduper, hash)

    def test_obj_id(self):
        """Test filter_unique with objects using id as key, which fails."""
        # Two objects which may be equal do not necessary have the same id.
        deduped = set()
        deduper = tools.filter_unique(self.decs, container=deduped, key=id)
        self.assertIsEmpty(deduped)
        for _ in self.decs:
            self.assertEqual(id(next(deduper)), deduped.pop())
        with self.assertRaises(StopIteration):
            next(deduper)
        # len(Decimal with distinct ids) != len(Decimal with distinct value).
        deduper_ids = list(tools.filter_unique(self.decs, key=id))
        self.assertNotEqual(len(deduper_ids), len(set(deduper_ids)))

    def test_str(self):
        """Test filter_unique with str."""
        deduped = set()
        deduper = tools.filter_unique(self.strs, container=deduped)
        self._test_dedup_str(deduped, deduper)

    def test_str_hash(self):
        """Test filter_unique with str using hash as key."""
        deduped = set()
        deduper = tools.filter_unique(self.strs, container=deduped, key=hash)
        self._test_dedup_str(deduped, deduper, hash)

    def test_for_resumable(self):
        """Test filter_unique is resumable after a for loop."""
        gen2 = tools.filter_unique(self.ints)
        deduped = []
        for item in gen2:
            deduped.append(item)
            if len(deduped) == 3:
                break
        self.assertEqual(deduped, [1, 3, 2])
        last = next(gen2)
        self.assertEqual(last, 4)
        with self.assertRaises(StopIteration):
            next(gen2)

    def test_skip(self):
        """Test filter_unique with a container that skips items."""
        deduped = SkipList()
        deduper = tools.filter_unique(self.ints, container=deduped)
        deduped_out = list(deduper)
        self.assertCountEqual(deduped, deduped_out)
        self.assertEqual(deduped, {2, 4})

    def test_process_again(self):
        """Test filter_unique with an ignoring container."""
        deduped = ProcessAgainList()
        deduper = tools.filter_unique(self.ints, container=deduped)
        deduped_out = list(deduper)
        self.assertEqual(deduped_out, [1, 3, 2, 1, 1, 4])
        self.assertEqual(deduped, {2, 4})

    def test_stop(self):
        """Test filter_unique with an ignoring container."""
        deduped = ContainsStopList()
        deduped.stop_list = [2]
        deduper = tools.filter_unique(self.ints, container=deduped)
        deduped_out = list(deduper)
        self.assertCountEqual(deduped, deduped_out)
        self.assertEqual(deduped, {1, 3})

        # And it should not resume
        with self.assertRaises(StopIteration):
            next(deduper)

        deduped = AddStopList()
        deduped.stop_list = [4]
        deduper = tools.filter_unique(self.ints, container=deduped)
        deduped_out = list(deduper)
        self.assertCountEqual(deduped, deduped_out)
        self.assertEqual(deduped, {1, 2, 3})

        # And it should not resume
        with self.assertRaises(StopIteration):
            next(deduper)


class TestFileModeChecker(TestCase):

    """Test parsing password files."""

    net = False

    def patch(self, name):
        """Patch up <name> in self.setUp."""
        patcher = mock.patch(name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def setUp(self):
        """Patch a variety of dependencies."""
        super().setUp()
        self.stat = self.patch('os.stat')
        self.chmod = self.patch('os.chmod')
        self.file = '~FakeFile'

    def test_auto_chmod_for_dir(self):
        """Do not chmod files that have mode private_files_permission."""
        self.stat.return_value.st_mode = 0o040600  # dir
        tools.file_mode_checker(self.file, mode=0o600)
        self.stat.assert_called_with(self.file)
        self.assertFalse(self.chmod.called)

    def test_auto_chmod_OK(self):
        """Do not chmod files that have mode private_files_permission."""
        self.stat.return_value.st_mode = 0o100600  # regular file
        tools.file_mode_checker(self.file, mode=0o600)
        self.stat.assert_called_with(self.file)
        self.assertFalse(self.chmod.called)

    def test_auto_chmod_not_OK(self):
        """Chmod files that do not have mode private_files_permission."""
        self.stat.return_value.st_mode = 0o100644  # regular file
        tools.file_mode_checker(self.file, mode=0o600)
        self.stat.assert_called_with(self.file)
        self.chmod.assert_called_once_with(self.file, 0o600)


class TestFileShaCalculator(TestCase):

    r"""Test calculator of sha of a file.

    There are two possible hash values for each test. The second one is for
    files with Windows line endings (\r\n).

    """

    net = False

    filename = join_xml_data_path('article-pear-0.10.xml')

    def test_md5_complete_calculation(self):
        """Test md5 of complete file."""
        res = tools.compute_file_hash(self.filename, sha='md5')
        self.assertIn(res, (
            '5d7265e290e6733e1e2020630262a6f3',
            '2c941f2fa7e6e629d165708eb02b67f7',
        ))

    def test_md5_partial_calculation(self):
        """Test md5 of partial file (1024 bytes)."""
        res = tools.compute_file_hash(self.filename, sha='md5',
                                      bytes_to_read=1024)
        self.assertIn(res, (
            'edf6e1accead082b6b831a0a600704bc',
            'be0227b6d490baa49e6d7e131c7f596b',
        ))

    def test_sha1_complete_calculation(self):
        """Test sha1 of complete file."""
        res = tools.compute_file_hash(self.filename, sha='sha1')
        self.assertIn(res, (
            '1c12696e1119493a625aa818a35c41916ce32d0c',
            '146121e6d0461916c9a0fab00dc718acdb6a6b14',
        ))

    def test_sha1_partial_calculation(self):
        """Test sha1 of partial file (1024 bytes)."""
        res = tools.compute_file_hash(self.filename, sha='sha1',
                                      bytes_to_read=1024)
        self.assertIn(res, (
            'e56fa7bd5cfdf6bb7e2d8649dd9216c03e7271e6',
            '617ce7d539848885b52355ed597a042dae1e726f',
        ))

    def test_sha224_complete_calculation(self):
        """Test sha224 of complete file."""
        res = tools.compute_file_hash(self.filename, sha='sha224')
        self.assertIn(res, (
            '3d350d9d9eca074bd299cb5ffe1b325a9f589b2bcd7ba1c033ab4d33',
            '4a2cf33b7da01f7b0530b2cc624e1180c8651b20198e9387aee0c767',
        ))

    def test_sha224_partial_calculation(self):
        """Test sha224 of partial file (1024 bytes)."""
        res = tools.compute_file_hash(self.filename, sha='sha224',
                                      bytes_to_read=1024)
        self.assertIn(res, (
            'affa8cb79656a9b6244a079f8af91c9271e382aa9d5aa412b599e169',
            '486467144e683aefd420d576250c4cc984e6d7bf10c85d36e3d249d2',
        ))


class Foo:

    """Test class to verify classproperty decorator."""

    _bar = 'baz'

    @classproperty
    def bar(cls):
        """Class property method."""
        return cls._bar


class TestClassProperty(TestCase):

    """Test classproperty decorator."""

    net = False

    def test_classproperty(self):
        """Test for classproperty decorator."""
        self.assertEqual(Foo.bar, 'baz')
        self.assertEqual(Foo.bar, Foo._bar)


class TestMergeGenerator(TestCase):

    """Test merging generators."""

    net = False

    def test_roundrobin_generators(self):
        """Test merge_generators generator."""
        gen = range(5)
        result = list(tools.roundrobin_generators(gen, 'ABC'))
        self.assertEqual(result, [0, 'A', 1, 'B', 2, 'C', 3, 4])
        result = ''.join(tools.roundrobin_generators('HlWrd', 'e', 'lool'))
        self.assertEqual(result, 'HelloWorld')


class TestIsIpAddress(TestCase):

    """Unit test class for is_ip_address."""

    net = False

    def test_valid_ipv4_addresses(self):
        """Check with valid IPv4 addresses."""
        valid_addresses = (
            '0.0.0.0',
            '1.2.3.4',
            '1.2.3.4',
            '192.168.0.1',
            '255.255.255.255',
        )

        for address in valid_addresses:
            with self.subTest(ip_address=address):
                self.assertTrue(is_ip_address(address))

    def test_invalid_ipv4_addresses(self):
        """Check with invalid IPv4 addresses."""
        invalid_addresses = (
            None,
            '',
            '0.0.0',
            '1.2.3.256',
            '1.2.3.-1',
            '0.0.0.a',
            'a.b.c.d',
        )

        for address in invalid_addresses:
            with self.subTest(ip_address=address):
                self.assertFalse(is_ip_address(address))

    def test_valid_ipv6_addresses(self):
        """Check with valid IPv6 addresses."""
        valid_addresses = (
            'fe80:0000:0000:0000:0202:b3ff:fe1e:8329',
            'fe80:0:0:0:202:b3ff:fe1e:8329',
            'fe80::202:b3ff:fe1e:8329',
            '::ffff:5.9.158.75',
            '::',
        )

        for address in valid_addresses:
            with self.subTest(ip_address=address):
                self.assertTrue(is_ip_address(address))

    def test_invalid_ipv6_addresses(self):
        """Check with invalid IPv6 addresses."""
        invalid_addresses = (
            None,
            '',
            ':',
            ':::',
            '2001:db8::aaaa::1',
            'fe80:0000:0000:0000:0202:b3ff:fe1e: 8329',
            'fe80:0000:0000:0000:0202:b3ff:fe1e:829g',
        )

        for address in invalid_addresses:
            with self.subTest(ip_address=address):
                self.assertFalse(is_ip_address(address))


class TestHasModule(TestCase):

    """Unit test class for has_module."""

    net = False

    def test_when_present(self):
        """Test when the module is available."""
        self.assertTrue(has_module('setuptools'))
        self.assertTrue(has_module('setuptools', '1.0'))

    def test_when_missing(self):
        """Test when the module is unavailable."""
        self.assertFalse(has_module('no-such-module'))

    @suppress_warnings(
        r'^Module version .* is lower than requested version 99999$',
        ImportWarning)
    def test_when_insufficient_version(self):
        """Test when the module is older than what we need."""
        self.assertFalse(has_module('setuptools', '99999'))


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
