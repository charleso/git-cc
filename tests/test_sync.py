import filecmp
import os
import shutil
import sys
import stat
import unittest

from git_cc.common import GitConfigParser
from git_cc.sync import Sync
from git_cc.sync import SyncFile
from git_cc.sync import ClearCaseSync
from git_cc.sync import output_as_set

if sys.version_info[0] == 2:
    from mock import Mock
elif sys.version_info[0] == 3:
    if sys.version_info[1] < 3:
        from mock import Mock
    else:
        from unittest.mock import Mock

_current_dir = os.path.dirname(__file__)


class CopyTestSuite(unittest.TestCase):

    def setUp(self):

        self.clear_filecmp_cache()

        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.src_dir = os.path.join(current_dir, "copy-data")
        self.dst_dir = os.path.join(current_dir, "sandbox")

        if os.path.exists(self.dst_dir):
            shutil.rmtree(self.dst_dir)

        os.mkdir(self.dst_dir)

    def tearDown(self):
        shutil.rmtree(self.dst_dir)

    def test_copy_creates_new_file(self):

        fileName = "a.txt"

        copyIsDone = SyncFile().do_sync(
            fileName, src_dir=self.src_dir, dst_dir=self.dst_dir)
        self.assertTrue(copyIsDone)
        src_path = os.path.join(self.src_dir, fileName)
        dst_path = os.path.join(self.dst_dir, fileName)
        self.files_are_equal(src_path, dst_path)

    def test_copy_overwrites_existing_different_file(self):

        fileName = "a.txt"

        src_path = os.path.join(self.src_dir, fileName)
        with open(src_path, "r") as f:
            lines = f.readlines()
        lines[0] = lines[0].replace('e', 'f')

        dst_path = os.path.join(self.dst_dir, fileName)
        with open(dst_path, "w") as f:
            f.writelines(lines)

        # to make it more difficult, we give the destination file the same
        # file stats
        shutil.copystat(src_path, dst_path)

        copyIsDone = SyncFile().do_sync(
            fileName, src_dir=self.src_dir, dst_dir=self.dst_dir)
        self.assertTrue(copyIsDone)
        self.files_are_equal(src_path, dst_path)

    def test_copy_does_not_overwrite_equal_file(self):

        fileName = "a.txt"

        src_path = os.path.join(self.src_dir, fileName)
        dst_path = os.path.join(self.dst_dir, fileName)

        shutil.copyfile(src_path, dst_path)
        self.assertTrue(os.path.exists(dst_path))

        # We make the destination file read-only. If the copy statement throws
        # an exception, it did not recognize that the destination file was the
        # same and tried to copy it.
        os.chmod(dst_path, stat.S_IREAD)

        copyIsDone = SyncFile().do_sync(
            fileName, src_dir=self.src_dir, dst_dir=self.dst_dir)
        self.assertFalse(copyIsDone)

    def files_are_equal(self, src_path, dst_path):

        self.clear_filecmp_cache()

        self.assertTrue(filecmp.cmp(src_path, dst_path))

        src_stats = os.stat(src_path)
        dst_stats = os.stat(dst_path)
        self.assertAlmostEqual(src_stats.st_mtime, dst_stats.st_mtime,
                               places=2)

    def clear_filecmp_cache(self):
        """Clear the cache of module filecmp to trigger new file comparisons.

        Module filecmp keeps a cache of file comparisons so it does not have to
        recompare files whose stats have not changed. This disrupts tests in
        this suite which compare files with the same paths and stats but with
        different contents. For that reason, we can clear the cache.

        Do note that this function uses an internal variable of filecmp and can
        break when that variable is removed, renamed etc.

        """
        filecmp._cache = {}


class SyncTestSuite(unittest.TestCase):

    def setUp(self):

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.dst_root = os.path.join(self.current_dir, "sandbox")

        if os.path.exists(self.dst_root):
            shutil.rmtree(self.dst_root)

        os.mkdir(self.dst_root)

    def tearDown(self):
        shutil.rmtree(self.dst_root)

    def test_sync_copies_directory_tree(self):

        self.src_root = os.path.join(self.current_dir, "sync-data/simple-tree")
        src_dirs = ["."]

        sync = Sync(self.src_root, src_dirs, self.dst_root)
        sync.do_sync()

        dircmp = filecmp.dircmp(self.src_root, self.dst_root)

        self.assertEqual(dircmp.left_only, [])
        self.assertEqual(dircmp.right_only, [])
        self.assertEqual(dircmp.diff_files, [])

    def test_clearcase_sync_copies_directory_tree(self):

        self.src_root = os.path.join(
            self.current_dir, "sync-data", "simple-tree")
        src_dirs = ["."]

        sync = ClearCaseSync(self.src_root, src_dirs, self.dst_root)
        sync.collect_private_files = Mock(return_value={})
        sync.do_sync()

        dircmp = filecmp.dircmp(self.src_root, self.dst_root)

        self.assertEqual(dircmp.left_only, ['lost+found'])
        self.assertEqual(dircmp.right_only, [])
        self.assertEqual(dircmp.diff_files, [])

    def test_clearcase_sync_copies_directory_tree_without_private_files(self):

        self.src_root = os.path.join(
            self.current_dir, "sync-data", "simple-tree")
        src_dirs = ["."]

        sync = ClearCaseSync(self.src_root, src_dirs, self.dst_root)
        private_file = os.path.join(self.src_root, "subdir", "b.txt")
        sync.collect_private_files = Mock(return_value={private_file: 1})
        sync.do_sync()

        dircmp = filecmp.dircmp(self.src_root, self.dst_root)

        self.assertEqual(
            sorted(dircmp.left_only), sorted(["lost+found", "subdir"]))
        self.assertEqual(dircmp.right_only, [])
        self.assertEqual(dircmp.diff_files, [])


class CollectCommandOutputSuite(unittest.TestCase):

    def test_collect_output(self):

        current_dir = os.path.dirname(os.path.abspath(__file__))
        module = os.path.join(current_dir, "print_dir.py")
        directory = os.path.join(current_dir, "output-as-set-data")
        contents = output_as_set([sys.executable, module, directory])

        self.assertEqual(set(["a.txt", "b.txt"]), contents)


class SyncConfigTestSuite(unittest.TestCase):

    def test_retrieval_of_setting_using_config(self):

        gitcc_config_path = self.get_path_to("gitcc")

        cfg = GitConfigParser("don't care section", gitcc_config_path)
        cfg.read()

        self.assertTrue(cfg.ignorePrivateFiles())

    def test_retrieval_of_setting_using_empty_config(self):

        gitcc_config_path = self.get_path_to("gitcc-empty")

        cfg = GitConfigParser("don't care section", gitcc_config_path)
        cfg.read()

        self.assertFalse(cfg.ignorePrivateFiles())

    def get_path_to(self, file_name):
        """Return the path to the given file in directory "sync-config".

        Directory "sync-config" is located in the same directory as the current
        file.

        """
        return os.path.join(_current_dir, "sync-config", file_name)
