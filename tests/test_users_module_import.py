import os
import unittest

from git_cc.common import get_users_module
from git_cc.common import GitConfigParser

_current_dir = os.path.dirname(__file__)


class UsersModuleImportTestSuite(unittest.TestCase):

    def test_import_of_users_module(self):

        users_module_path = self.get_path_to("users.py")
        users = get_users_module(users_module_path)

        self.assertEqual(users.users["charleso"], "Charles O'Farrell")
        self.assertEqual(users.users["jki"], "Jan Kiszka <jan.kiszka@web.de>")
        self.assertEqual(users.mailSuffix, "example.com")

    def test_import_of_nonexisting_users_module(self):

        users_module_path = self.get_path_to("nonexisting.py")
        users = get_users_module(users_module_path)

        self.assertEqual(users.users, {})
        self.assertEqual(users.mailSuffix, "")

    def test_import_of_unspecified_users_module(self):

        users = get_users_module("")

        self.assertEqual(users.users, {})
        self.assertEqual(users.mailSuffix, "")

    def test_retrieval_of_absolute_users_module_path(self):

        gitcc_config_path = self.get_path_to("gitcc-abs")

        cfg = GitConfigParser("don't care section", gitcc_config_path)
        cfg.read()

        abs_path = "/home/user/gitcc/users.py"
        self.assertEqual(abs_path, cfg.getUsersModulePath())

    def test_retrieval_of_relative_users_module_path(self):

        gitcc_config_path = self.get_path_to("gitcc")

        cfg = GitConfigParser("don't care section", gitcc_config_path)
        cfg.read()

        abs_path = os.path.join(_current_dir, "user-config", "users.py")
        self.assertEqual(abs_path, cfg.getUsersModulePath())

    def test_retrieval_of_users_using_config(self):

        gitcc_config_path = self.get_path_to("gitcc")

        cfg = GitConfigParser("don't care section", gitcc_config_path)
        cfg.read()

        users = get_users_module(cfg.getUsersModulePath())

        self.assertEqual(users.users["charleso"], "Charles O'Farrell")
        self.assertEqual(users.users["jki"], "Jan Kiszka <jan.kiszka@web.de>")
        self.assertEqual(users.mailSuffix, "example.com")

    def test_retrieval_of_users_using_empty_config(self):

        gitcc_config_path = self.get_path_to("gitcc-empty")

        cfg = GitConfigParser("don't care section", gitcc_config_path)
        cfg.read()

        users = get_users_module(cfg.getUsersModulePath())

        self.assertEqual(users.users, {})
        self.assertEqual(users.mailSuffix, "")

    def get_path_to(self, file_name):
        """Return the path to the given file in directory "user-config".

        Directory "user-config" is located in the same directory as the current
        file.

        """
        return os.path.join(_current_dir, "user-config", file_name)
