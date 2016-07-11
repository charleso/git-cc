import filecmp
import os
import shutil
import stat
import unittest


from git_cc.sync import copy


class SyncTestSuite(unittest.TestCase):

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

        copyIsDone = copy(fileName, src_dir=self.src_dir, dst_dir=self.dst_dir)
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

        copyIsDone = copy(fileName, src_dir=self.src_dir, dst_dir=self.dst_dir)
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

        copyIsDone = copy(fileName, src_dir=self.src_dir, dst_dir=self.dst_dir)
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
