#!/usr/bin/env python3
"""Test tools package alone which don't fit into other tests."""
#
# (C) Pywikibot team, 2015-2023
#
# Distributed under the terms of the MIT license.
import decimal
import os
import subprocess
import tempfile
import unittest
from collections import Counter, OrderedDict
from collections.abc import Mapping
from contextlib import suppress
from unittest import mock

from pywikibot import config, tools
from pywikibot.tools import (
    cached,
    classproperty,
    has_module,
    is_ip_address,
    suppress_warnings,
)
from pywikibot.tools.itertools import (
    filter_unique,
    intersect_generators,
    islice_with_ellipsis,
    roundrobin_generators,
)
from tests import join_xml_data_path
from tests.aspects import TestCase
from tests.utils import skipping


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

    def test_open_archive_gz(self):
        """Test open_archive with gz compressor in the standard library."""
        self.assertEqual(
            self._get_content(self.base_file + '.gz'), self.original_content)

    def test_open_archive_7z(self):
        """Test open_archive with 7za if installed."""
        with skipping(OSError, msg='7za not installed'):
            subprocess.Popen(['7za'], stdout=subprocess.PIPE).stdout.close()

        self.assertEqual(
            self._get_content(self.base_file + '.7z'), self.original_content)
        with self.assertRaisesRegex(
                OSError,
                'Unexpected STDERR output from 7za '):
            self._get_content(self.base_file + '_invalid.7z',
                              use_extension=True)

    def test_open_archive_lzma(self):
        """Test open_archive with lzma compressor in the standard library."""
        self.assertEqual(
            self._get_content(self.base_file + '.lzma'), self.original_content)
        # Legacy LZMA container formet has no magic, skipping
        # use_extension=False test here
        self.assertEqual(
            self._get_content(self.base_file + '.xz'), self.original_content)
        self.assertEqual(
            self._get_content(self.base_file + '.xz', use_extension=False),
            self.original_content)


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
        content = self._write_content('.lzma')
        with open(self.base_file + '.lzma', 'rb') as f:
            self.assertEqual(content, f.read())

    def test_write_archive_xz(self):
        """Test writing a xz archive."""
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
        it = list(islice_with_ellipsis(self.it, stop))
        self.assertLength(it, stop + 1)  # +1 to consider marker.
        self.assertEqual(it[:-1], self.it[:stop])
        self.assertEqual(it[-1], '…')

    def test_show_custom_marker(self):
        """Test correct marker is shown with kwargs.."""
        stop = 2
        it = list(islice_with_ellipsis(self.it, stop, marker='new'))
        self.assertLength(it, stop + 1)  # +1 to consider marker.
        self.assertEqual(it[:-1], self.it[:stop])
        self.assertNotEqual(it[-1], '…')
        self.assertEqual(it[-1], 'new')

    def test_show_marker_with_start_stop(self):
        """Test marker is shown with start and stop without kwargs."""
        start = 1
        stop = 3
        it = list(islice_with_ellipsis(self.it, start, stop))
        self.assertLength(it, stop - start + 1)  # +1 to consider marker.
        self.assertEqual(it[:-1], self.it[start:stop])
        self.assertEqual(it[-1], '…')

    def test_show_custom_marker_with_start_stop(self):
        """Test marker is shown with start and stop with kwargs."""
        start = 1
        stop = 3
        it = list(islice_with_ellipsis(self.it, start, stop, marker='new'))
        self.assertLength(it, stop - start + 1)  # +1 to consider marker.
        self.assertEqual(it[:-1], self.it[start:stop])
        self.assertNotEqual(it[-1], '…')
        self.assertEqual(it[-1], 'new')

    def test_show_marker_with_stop_zero(self):
        """Test marker is shown with stop for non empty iterable."""
        stop = 0
        it = list(islice_with_ellipsis(self.it, stop))
        self.assertLength(it, stop + 1)  # +1 to consider marker.
        self.assertEqual(it[-1], '…')

    def test_do_not_show_marker_with_stop_zero(self):
        """Test marker is shown with stop for empty iterable."""
        stop = 0
        it = list(islice_with_ellipsis(self.it_null, stop))
        self.assertLength(it, stop)

    def test_do_not_show_marker(self):
        """Test marker is not shown when no marker is specified."""
        import itertools
        stop = 2
        it_1 = list(islice_with_ellipsis(self.it, stop, marker=None))
        it_2 = list(itertools.islice(self.it, stop))
        self.assertEqual(it_1, it_2)  # same behavior as islice().

    def test_do_not_show_marker_when_get_all(self):
        """Test marker is not shown when all elements are retrieved."""
        stop = None
        it = list(islice_with_ellipsis(self.it, stop))
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

        super().add(item)


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
        deduper = filter_unique(self.ints, container=deduped)
        self._test_dedup_int(deduped, deduper)

    def test_dict(self):
        """Test filter_unique with a dict."""
        deduped = {}
        deduper = filter_unique(self.ints, container=deduped)
        self._test_dedup_int(deduped, deduper)

    def test_OrderedDict(self):
        """Test filter_unique with an OrderedDict."""
        deduped = OrderedDict()
        deduper = filter_unique(self.ints, container=deduped)
        self._test_dedup_int(deduped, deduper)

    def test_int_hash(self):
        """Test filter_unique with ints using hash as key."""
        deduped = set()
        deduper = filter_unique(self.ints, container=deduped, key=hash)
        self._test_dedup_int(deduped, deduper, hash)

    def test_int_id(self):
        """Test filter_unique with ints using id as key."""
        deduped = set()
        deduper = filter_unique(self.ints, container=deduped, key=id)
        self._test_dedup_int(deduped, deduper, id)

    def test_obj(self):
        """Test filter_unique with objects."""
        deduped = set()
        deduper = filter_unique(self.decs, container=deduped)
        self._test_dedup_int(deduped, deduper)

    def test_obj_hash(self):
        """Test filter_unique with objects using hash as key."""
        deduped = set()
        deduper = filter_unique(self.decs, container=deduped, key=hash)
        self._test_dedup_int(deduped, deduper, hash)

    def test_obj_id(self):
        """Test filter_unique with objects using id as key, which fails."""
        # Two objects which may be equal do not necessary have the same id.
        deduped = set()
        deduper = filter_unique(self.decs, container=deduped, key=id)
        self.assertIsEmpty(deduped)
        for _ in self.decs:
            self.assertEqual(id(next(deduper)), deduped.pop())
        with self.assertRaises(StopIteration):
            next(deduper)
        # len(Decimal with distinct ids) != len(Decimal with distinct value).
        deduper_ids = list(filter_unique(self.decs, key=id))
        self.assertNotEqual(len(deduper_ids), len(set(deduper_ids)))

    def test_str(self):
        """Test filter_unique with str."""
        deduped = set()
        deduper = filter_unique(self.strs, container=deduped)
        self._test_dedup_str(deduped, deduper)

    def test_str_hash(self):
        """Test filter_unique with str using hash as key."""
        deduped = set()
        deduper = filter_unique(self.strs, container=deduped, key=hash)
        self._test_dedup_str(deduped, deduper, hash)

    def test_for_resumable(self):
        """Test filter_unique is resumable after a for loop."""
        gen2 = filter_unique(self.ints)
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
        deduper = filter_unique(self.ints, container=deduped)
        deduped_out = list(deduper)
        self.assertCountEqual(deduped, deduped_out)
        self.assertEqual(deduped, {2, 4})

    def test_process_again(self):
        """Test filter_unique with an ignoring container."""
        deduped = ProcessAgainList()
        deduper = filter_unique(self.ints, container=deduped)
        deduped_out = list(deduper)
        self.assertEqual(deduped_out, [1, 3, 2, 1, 1, 4])
        self.assertEqual(deduped, {2, 4})

    def test_stop_contains(self):
        """Test filter_unique with an ignoring container."""
        deduped = ContainsStopList()
        deduped.stop_list = [2]
        deduper = filter_unique(self.ints, container=deduped)
        deduped_out = list(deduper)
        self.assertCountEqual(deduped, deduped_out)
        self.assertEqual(deduped, {1, 3})

        # And it should not resume
        with self.assertRaises(StopIteration):
            next(deduper)

    def test_stop_add(self):
        """Test filter_unique with an ignoring container during add call."""
        deduped = AddStopList()
        deduped.stop_list = [4]
        deduper = filter_unique(self.ints, container=deduped)
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
        tools.file_mode_checker(self.file,
                                mode=config.private_folder_permission)
        self.stat.assert_called_with(self.file)
        self.assertFalse(self.chmod.called)

    def test_auto_chmod_OK(self):
        """Do not chmod files that have mode private_files_permission."""
        self.stat.return_value.st_mode = 0o100600  # regular file
        tools.file_mode_checker(self.file,
                                mode=config.private_files_permission)
        self.stat.assert_called_with(self.file)
        self.assertFalse(self.chmod.called)

    def test_auto_chmod_not_OK(self):
        """Chmod files that do not have mode private_files_permission."""
        self.stat.return_value.st_mode = 0o100644  # regular file
        tools.file_mode_checker(self.file,
                                mode=config.private_files_permission)
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


class GeneratorIntersectTestCase(TestCase):

    """Base class for intersect_generators test cases."""

    def assertEqualItertools(self, gens):
        """Assert intersect_generators result is same as set intersection."""
        # If they are a generator, we need to convert to a list
        # first otherwise the generator is empty the second time.
        datasets = [list(gen) for gen in gens]
        set_result = set(datasets[0]).intersection(*datasets[1:])
        result = list(intersect_generators(*datasets))

        self.assertCountEqual(set(result), result)
        self.assertCountEqual(result, set_result)

    def assertEqualItertoolsWithDuplicates(self, gens):
        """Assert intersect_generators result equals Counter intersection."""
        # If they are a generator, we need to convert to a list
        # first otherwise the generator is empty the second time.
        datasets = [list(gen) for gen in gens]
        counter_result = Counter(datasets[0])
        for dataset in datasets[1:]:
            counter_result = counter_result & Counter(dataset)
        counter_result = list(counter_result.elements())
        result = list(intersect_generators(*datasets, allow_duplicates=True))
        self.assertCountEqual(counter_result, result)


class BasicGeneratorIntersectTestCase(GeneratorIntersectTestCase):

    """Disconnected intersect_generators test cases."""

    net = False

    def test_intersect_basic(self):
        """Test basic intersect without duplicates."""
        self.assertEqualItertools(['abc', 'db', 'ba'])

    def test_intersect_with_dups(self):
        """Test basic intersect with duplicates."""
        self.assertEqualItertools(['aabc', 'dddb', 'baa'])

    def test_intersect_with_accepted_dups(self):
        """Test intersect with duplicates accepted."""
        self.assertEqualItertoolsWithDuplicates(['abc', 'db', 'ba'])
        self.assertEqualItertoolsWithDuplicates(['aabc', 'dddb', 'baa'])
        self.assertEqualItertoolsWithDuplicates(['abb', 'bb'])
        self.assertEqualItertoolsWithDuplicates(['bb', 'abb'])
        self.assertEqualItertoolsWithDuplicates(['abbcd', 'abcba'])
        self.assertEqualItertoolsWithDuplicates(['abcba', 'abbcd'])


class TestMergeGenerator(TestCase):

    """Test merging generators."""

    net = False

    def test_roundrobin_generators(self):
        """Test merge_generators generator."""
        gen = range(5)
        result = list(roundrobin_generators(gen, 'ABC'))
        self.assertEqual(result, [0, 'A', 1, 'B', 2, 'C', 3, 4])
        result = ''.join(roundrobin_generators('HlWrd', 'e', 'lool'))
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


class TestStringFunctions(TestCase):

    """Unit test class for string functions."""

    net = False

    def test_first_lower(self):
        """Test first_lower function."""
        self.assertEqual(tools.first_lower('Foo Bar'), 'foo Bar')
        self.assertEqual(tools.first_lower('FOO BAR'), 'fOO BAR')
        self.assertEqual(tools.first_lower(''), '')

    def test_first_upper(self):
        """Test first_upper function."""
        self.assertEqual(tools.first_upper('foo bar'), 'Foo bar')
        self.assertEqual(tools.first_upper('foo BAR'), 'Foo BAR')
        self.assertEqual(tools.first_upper(''), '')
        self.assertEqual(tools.first_upper('ß'), 'ß')
        self.assertNotEqual(tools.first_upper('ß'), str.upper('ß'))

    def test_strtobool(self):
        """Test strtobool function."""
        for string in ('True', 'TRUE', 'true', 'T', 'Yes', 'y', 'on', '1'):
            with self.subTest(truth=string):
                self.assertTrue(tools.strtobool(string))
        for string in ('False', 'F', 'No', 'n', 'oFF', '0'):
            with self.subTest(falsity=string):
                self.assertFalse(tools.strtobool(string))
        with self.assertRaises(ValueError):
            tools.strtobool('okay')


class DecoratedMethods:

    """Test class to verify cached decorator."""

    def __init__(self):
        """Initializer, reset read counter."""
        self.read = 0

    @cached
    def foo(self):
        """A method."""
        self.read += 1
        return 'foo'

    @property
    @cached
    def bar(self):
        """A property."""
        self.read += 1
        return 'bar'

    def baz(self):
        """An undecorated method."""
        self.read += 1
        return 'baz'

    @cached
    def quux(self, force=False):
        """Method with force."""
        self.read += 1
        return 'quux'

    @cached
    def method_with_args(self, *args, **kwargs):
        """Method with force."""
        self.read += 1
        return 'method_with_args'


class TestTinyCache(TestCase):

    """Test cached decorator."""

    net = False

    def setUp(self):
        """Setup tests."""
        self.foo = DecoratedMethods()
        super().setUp()

    def test_cached(self):
        """Test for cached decorator."""
        self.assertEqual(self.foo.foo(), 'foo')  # check computed value
        self.assertEqual(self.foo.read, 1)
        self.assertTrue(hasattr(self.foo, '_foo'))
        self.assertEqual(self.foo.foo(), 'foo')  # check cached value
        self.assertEqual(self.foo.read, 1)  # bar() was called only once
        del self.foo._foo
        self.assertFalse(hasattr(self.foo, '_foo'))
        self.assertEqual(self.foo.foo(), 'foo')  # check computed value
        self.assertEqual(self.foo.__doc__,
                         'Test class to verify cached decorator.')
        self.assertEqual(self.foo.foo.__doc__, 'A method.')

    def test_cached_property(self):
        """Test for cached property decorator."""
        self.assertEqual(self.foo.bar, 'bar')
        self.assertEqual(self.foo.read, 1)
        self.assertTrue(hasattr(self.foo, '_bar'))
        self.assertEqual(self.foo.bar, 'bar')
        self.assertEqual(self.foo.read, 1)

    def test_cached_with_paramters(self):
        """Test for cached decorator with parameters."""
        msg = '"cached" decorator must be used without arguments'
        with self.assertRaisesRegex(TypeError, msg):
            cached(42)(self.foo.baz())
        with self.assertRaisesRegex(TypeError, msg):
            cached()(self.foo.baz())

    def test_cached_with_force(self):
        """Test for cached decorator with force enabled."""
        self.assertEqual(self.foo.quux(), 'quux')
        self.assertEqual(self.foo.read, 1)
        self.assertTrue(hasattr(self.foo, '_quux'))
        self.assertEqual(self.foo.quux(force=True), 'quux')
        self.assertEqual(self.foo.read, 2)

    def test_cached_with_argse(self):
        """Test method with args."""
        self.assertEqual(self.foo.method_with_args(force=False),
                         'method_with_args')
        self.assertEqual(self.foo.read, 1)
        self.assertTrue(hasattr(self.foo, '_method_with_args'))
        with self.assertRaises(TypeError):
            self.foo.method_with_args(True)
        with self.assertRaises(TypeError):
            self.foo.method_with_args(bar='baz')
        with self.assertRaises(TypeError):
            self.foo.method_with_args(1, 2, foo='bar')
        self.assertEqual(self.foo.method_with_args(force=True),
                         'method_with_args')
        self.assertEqual(self.foo.method_with_args(), 'method_with_args')
        self.assertEqual(self.foo.read, 2)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
