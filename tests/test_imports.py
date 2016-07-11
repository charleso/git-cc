import os
import imp
import pkgutil
import sys
import unittest


class ImportTestSuite(unittest.TestCase):

    def test_import_of_each_module(self):
        """Import each module of package git_cc.

        This test was added because the import Python 3 requires you to use the
        relative package import syntax "from . import <module name>" to import
        packages from the same package, whereas Python 2 you could just use
        "import <module name>".

        """
        import git_cc
        package_dir = os.path.dirname(os.path.abspath(git_cc.__file__))
        for _, module_name, _ in pkgutil.iter_modules([package_dir]):
            self.try_module_import(package_dir, module_name)

    def try_module_import(self, package_dir, module_name):
        """Try to import the given module from the given directory.

        If the import fails, this method throws an exception.

        Note that when the import was successful, this method immediately
        removes it from the list of loaded modules.

        """

        module_path = os.path.join(package_dir, module_name) + ".py"

        # The call to imp.load_source fails when it indirectly imports a
        # module that was already loaded by a previous call to
        # imp.load_source under the same name.
        #
        # To give an example, say you have the following pseudo-code:
        #
        #    imp.load_source("package.module-a", ... )
        #    imp.load_source("package.module-b", ... )
        #
        # and module-b has an import of module a, then the second call
        # throws an ImportError with the message that it cannot import name
        # "module-b".
        #
        # To avoid this issue, we remove the module from the list of imported
        # modules once the import has succeeded.

        full_module_name = "git_cc." + module_name
        imp.load_source(full_module_name, module_path)
        del sys.modules[full_module_name]
