import os
import pkgutil
import subprocess
import sys
import unittest


class ImportTestSuite(unittest.TestCase):

    def test_import_of_each_module(self):
        """Test whether the import each module of package git_cc succeeds.

        This test was added because the import Python 3 requires you to use the
        relative package import syntax "from . import <module name>" to import
        packages from the same package, whereas Python 2 you could just use
        "import <module name>".

        """
        import git_cc
        package_dir = os.path.dirname(os.path.abspath(git_cc.__file__))
        for _, module_name, _ in pkgutil.iter_modules([package_dir]):
            self.check_module_import(package_dir, module_name)

    def check_module_import(self, package_dir, module_name):
        """Return true if and only if the import of the given module succeeds.

        If the import fails, this method throws an exception.
        """

        # To test whether the given module can be imported, we start a new
        # Python process and let that process import the module. In this way
        # the current Python process is not affected by these trial imports.
        #
        # An earlier version of this test used the Python library 'imp' and
        # function 'load_source' to load the given module in the current Python
        # process. This lead to conflicts with the actual import of these
        # modules.

        full_module_name = "git_cc." + module_name
        subprocess.check_call(
            [sys.executable, "-c", "import " + full_module_name])
