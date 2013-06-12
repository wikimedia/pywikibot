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

    class TestTerminalOutput(unittest.TestCase):
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

        def test_output(self):
            pywikibot.output("output", toStdout=False)
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "output\n")

        def test_output(self):
            pywikibot.output("output", toStdout=True)
            self.assertEqual(newstdout.getvalue(), "output\n")
            self.assertEqual(newstderr.getvalue(), "")

        def test_warning(self):
            pywikibot.warning("warning")
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "WARNING: warning\n")

        def test_error(self):
            pywikibot.error("error")
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "ERROR: error\n")

        def test_log(self):
            pywikibot.log("log")
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "")

        def test_critical(self):
            pywikibot.critical("critical")
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "CRITICAL: critical\n")

        def test_debug(self):
            pywikibot.debug("debug", "test")
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "")

        def test_exception(self):
            class TestException(Exception):
                pass
            try:
                raise TestException("Testing Exception")
            except TestException:
                pywikibot.exception("exception")
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "ERROR: TestException: Testing Exception\n")

        def test_exception(self):
            class TestException(Exception):
                pass
            try:
                raise TestException("Testing Exception")
            except TestException:
                pywikibot.exception("exception", tb=True)
            self.assertEqual(newstdout.getvalue(), "")
            stderrlines = newstderr.getvalue().split("\n")
            self.assertEqual(stderrlines[0], "ERROR: TestException: Testing Exception")
            self.assertEqual(stderrlines[1], "Traceback (most recent call last):")
            self.assertEqual(stderrlines[3], """    raise TestException("Testing Exception")""")
            self.assertEqual(stderrlines[4], "TestException: Testing Exception")

            self.assertNotEqual(stderrlines[-1], "\n")

    class TestTerminalInput(unittest.TestCase):
        def setUp(self):
            patch()
            newstdout.truncate(0)
            newstderr.truncate(0)
            newstdin.truncate(0)

        def tearDown(self):
            unpatch()

        def testInput(self):
            newstdin.write("input to read\n")
            newstdin.seek(0)

            returned = pywikibot.input("question")

            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "question ")

            self.assertIsInstance(returned, unicode)
            self.assertEqual(returned, u"input to read")

        @unittest.expectedFailure
        def testInputChoiceDefault(self):
            newstdin.write("\n")
            newstdin.seek(0)

            returned = pywikibot.inputChoice("question", ["answer 1", "answer 2", "answer 3"], ["A", "N", "S"], "A")

            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "question ([A]nswer 1, a[N]swer 2, an[S]wer 3) ")

            self.assertIsInstance(returned, unicode)
            self.assertEqual(returned, "a")

        def testInputChoiceCapital(self):
            newstdin.write("N\n")
            newstdin.seek(0)

            returned = pywikibot.inputChoice("question", ["answer 1", "answer 2", "answer 3"], ["A", "N", "S"], "A")

            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "question ([A]nswer 1, a[N]swer 2, an[S]wer 3) ")

            self.assertIsInstance(returned, unicode)
            self.assertEqual(returned, "n")

        def testInputChoiceNonCapital(self):
            newstdin.write("n\n")
            newstdin.seek(0)

            returned = pywikibot.inputChoice("question", ["answer 1", "answer 2", "answer 3"], ["A", "N", "S"], "A")

            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "question ([A]nswer 1, a[N]swer 2, an[S]wer 3) ")

            self.assertIsInstance(returned, unicode)
            self.assertEqual(returned, "n")

        def testInputChoiceIncorrectAnswer(self):
            newstdin.write("X\nN\n")
            newstdin.seek(0)

            returned = pywikibot.inputChoice("question", ["answer 1", "answer 2", "answer 3"], ["A", "N", "S"], "A")

            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "question ([A]nswer 1, a[N]swer 2, an[S]wer 3) "*2)

            self.assertIsInstance(returned, unicode)
            self.assertEqual(returned, "n")

    class TestTerminalOutputColorUnix(unittest.TestCase):
        def setUp(self):
            patch()
            newstdout.truncate(0)
            newstderr.truncate(0)
            newstdin.truncate(0)

        def tearDown(self):
            unpatch()

        def testOutputColorizedText(self):
            pywikibot.config.colorized_output = True
            pywikibot.output(u"normal text \03{lightpurple}light purple text\03{default} normal text")
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "normal text \x1b[35;1mlight purple text\x1b[0m normal text\n\x1b[0m")

        @unittest.expectedFailure
        def testOutputNoncolorizedText(self):
            pywikibot.config.colorized_output = False
            pywikibot.output(u"normal text \03{lightpurple}light purple text\03{default} normal text")
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "normal text light purple text normal text ***")

        def testOutputNoncolorizedText_incorrect(self):
            ''' This test documents current (incorrect) behavior '''
            pywikibot.config.colorized_output = False
            pywikibot.output(u"normal text \03{lightpurple}light purple text\03{default} normal text")
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "normal text \x03{lightpurple}light purple text\x03{default} normal text\n")

        @unittest.expectedFailure
        def testOutputColorCascade(self):
            pywikibot.config.colorized_output = True
            pywikibot.output(u"normal text \03{lightpurple} light purple \03{lightblue} light blue \03{default} light purple \03{default} normal text")
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "normal text \x1b[35;1m light purple \x1b[94;1m light blue \x1b[35;1m light purple \x1b[0m normal text\n\x1b[0m")

        def testOutputColorCascade_incorrect(self):
            ''' This test documents current (incorrect) behavior '''
            pywikibot.config.colorized_output = True
            pywikibot.output(u"normal text \03{lightpurple} light purple \03{lightblue} light blue \03{default} light purple \03{default} normal text")
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "normal text \x1b[35;1m light purple \x1b[94;1m light blue \x1b[0m light purple \x1b[0m normal text\n\x1b[0m")
    
    class TestTerminalUnicodeUnix(unittest.TestCase):
        def setUp(self):
            patch()
            newstdout.truncate(0)
            newstderr.truncate(0)
            newstdin.truncate(0)

        def tearDown(self):
            unpatch()

        def testOutputUnicodeText(self):
            pywikibot.config.console_encoding = 'utf-8'
            pywikibot.output(u"Заглавная_страница")
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), u"Заглавная_страница\n".encode('utf-8'))

            
        def testInputUnicodeText(self):
            pywikibot.config.console_encoding = 'utf-8'
            newstdin.write(u"Заглавная_страница\n".encode('utf-8'))
            newstdin.seek(0)
            
            returned = pywikibot.input(u"Википедию? ")
            
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), u"Википедию?  ".encode('utf-8'))
            
            self.assertIsInstance(returned, unicode)
            self.assertEqual(returned, u"Заглавная_страница")
            
    class TestTransliterationUnix(unittest.TestCase):
        def setUp(self):
            patch()
            newstdout.truncate(0)
            newstderr.truncate(0)
            newstdin.truncate(0)

        def tearDown(self):
            unpatch()

        def testOutputUnicodeText(self):
            pywikibot.config.console_encoding = 'latin-1'
            pywikibot.config.colorized_output = True
            pywikibot.output(u"abcd АБГД αβγδ あいうえお")
            self.assertEqual(newstdout.getvalue(), "")
            self.assertEqual(newstderr.getvalue(), "abcd \x1b[33;1mA\x1b[0m\x1b[33;1mB\x1b[0m\x1b[33;1mG\x1b[0m\x1b[33;1mD\x1b[0m \x1b[33;1ma\x1b[0m\x1b[33;1mb\x1b[0m\x1b[33;1mg\x1b[0m\x1b[33;1md\x1b[0m \x1b[33;1ma\x1b[0m\x1b[33;1mi\x1b[0m\x1b[33;1mu\x1b[0m\x1b[33;1me\x1b[0m\x1b[33;1mo\x1b[0m\n\x1b[0m")

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

