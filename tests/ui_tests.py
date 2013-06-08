# -*- coding: utf-8  -*-
"""
Tests for the page module.
"""
#
# (C) Pywikipedia bot team, 2008
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: page_tests.py 11625 2013-06-08 19:55:59Z valhallasw $'


import unittest
import cStringIO
import StringIO
import logging

if __name__ == "__main__":
    import sys

    oldstderr = sys.stderr
    oldstdout = sys.stdout
    oldstdin = sys.stdin

    newstdout = cStringIO.StringIO()
    newstderr = cStringIO.StringIO()
    newstdin = StringIO.StringIO()

    def patch():
        sys.stdout = newstdout
        sys.stderr = newstderr
        sys.stdin = newstdin

    def unpatch():
        sys.stdout = oldstdout
        sys.stderr = oldstderr
        sys.stdin = oldstdin

    try:
        patch()
        import pywikibot
    finally:
        unpatch()

    from pywikibot.bot import DEBUG, VERBOSE, INFO, STDOUT, INPUT, WARNING, ERROR, CRITICAL

    logger = logging.getLogger('pywiki')
    loggingcontext = {'caller_name': "ui_tests",
                      'caller_file': "ui_tests",
                      'caller_line': 0,
                      'newline': "\n"}

    class TestTerminalUI(unittest.TestCase):
        def setUp(self):
            patch()
            newstdout.truncate(0)
            newstderr.truncate(0)
            newstdin.truncate(0)

        def tearDown(self):
            unpatch()

        def testOutputLevels_logging_debug(self):
            logger.log(DEBUG, 'debug', extra=loggingcontext)
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "")

        def testOutputLevels_logging_verbose(self):
            logger.log(VERBOSE, 'verbose', extra=loggingcontext)
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "")

        def testOutputLevels_logging_info(self):
            logger.log(INFO, 'info', extra=loggingcontext)
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "info\n")

        def testOutputLevels_logging_stdout(self):
            logger.log(STDOUT, 'stdout', extra=loggingcontext)
            self.assertEqual(newstdout.getvalue(), "stdout\n")
            self.assertEqual(newstderr.getvalue(), "")

        def testOutputLevels_logging_input(self):
            logger.log(INPUT, 'input', extra=loggingcontext)
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "input\n")

        def testOutputLevels_logging_WARNING(self):
            logger.log(WARNING, 'WARNING', extra=loggingcontext)
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "WARNING: WARNING\n")

        def testOutputLevels_logging_ERROR(self):
            logger.log(ERROR, 'ERROR', extra=loggingcontext)
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "ERROR: ERROR\n")

        def testOutputLevels_logging_CRITICAL(self):
            logger.log(CRITICAL, 'CRITICAL', extra=loggingcontext)
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "CRITICAL: CRITICAL\n")

    
    try:
        try:
            unittest.main()
        except SystemExit:
            pass
    finally:
        unpatch()
        pywikibot.stopme()

else:
    class TestTerminalUI(unittest.TestCase):
        @unittest.skip("Terminal UI tests can only be run by directly running tests/ui_tests.py")
        def testCannotBeRun(self):
            pass

