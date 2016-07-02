import sys
import unittest

from contextlib import contextmanager
from git_cc import __version__
from git_cc import version

if sys.version_info[0] == 2:
    from StringIO import StringIO
else:
    from io import StringIO


@contextmanager
def redirect_stdout():
    """Redirect sys.stdout to a StringIO and yield that StringIO.

    This function is a context manager that resets the redirect of sys.stdout
    to its original value on exit.

    Note that Python 3.4 has this function out-of-the-box, see
    contextlib.redirect_stdout. However, we also have to run using Python 2.x.

    """
    stdout = sys.stdout
    sys.stdout = StringIO()
    yield sys.stdout
    sys.stdout = stdout


class PrintVersionTestSuite(unittest.TestCase):

    def test_printed_version_is_the_correct_version(self):

        with redirect_stdout() as redirect:
            version.main()

        # do not forget to strip the newline from the redirected output
        self.assertEqual(__version__, redirect.getvalue().rstrip())
