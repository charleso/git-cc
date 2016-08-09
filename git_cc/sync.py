"""Copy files from Clearcase to Git manually"""

import filecmp
import os.path
import shutil
import stat
import subprocess
import sys

from fnmatch import fnmatch

from .cache import Cache
from .common import CC_DIR
from .common import GIT_DIR
from .common import cfg
from .common import debug
from .common import mkdirs
from .common import validateCC

ARGS = {
    'cache': 'Use the cache for faster syncing'
}


def copy(file_name, src_dir, dst_dir):
    """Copies the given file from its source to its destination directory.

    If the file already exists in the destination directory, this function only
    overwrites the destination file if the contents are different.

    This function returns True if and only if the file is actually copied.

    The destination file gets read and write permissions. It also gets the same
    last access time and last modification time as the source file.

    """
    src_file = os.path.join(src_dir, file_name)
    dst_file = os.path.join(dst_dir, file_name)
    copy_file = not os.path.exists(dst_file) or \
        not filecmp.cmp(src_file, dst_file, shallow=False)
    if copy_file:
        debug('Copying to %s' % dst_file)
        mkdirs(dst_file)
        shutil.copy2(src_file, dst_file)
        os.chmod(dst_file, stat.S_IREAD | stat.S_IWRITE)
    return copy_file


class Sync(object):
    """Implements the copying of a directory tree."""

    def __init__(self, src_root, dst_root):
        self.src_root = os.path.abspath(src_root)
        self.dst_root = os.path.abspath(dst_root)

    def do_sync(self):
        copied_file_count = 0
        for rel_dir, file_names in self.iter_src_files():
            for file_name in file_names:
                file_path = os.path.join(rel_dir, file_name)
                if copy(file_path, self.src_root, self.dst_root):
                    copied_file_count += 1
        return copied_file_count

    def iter_src_files(self):
        root_dir = self.src_root
        root_dir_length = len(root_dir)
        for abs_dir, _, file_names in os.walk(root_dir):
            rel_dir = abs_dir[root_dir_length + 1:]
            yield rel_dir, file_names


class ClearCaseSync(Sync):
    """Implements the copying of a directory tree under ClearCase control."""

    def iter_src_files(self):

        private_files = self.collect_private_files()

        def under_vc(rel_dir, file_name):
            path = os.path.join(rel_dir, file_name)
            return path not in private_files

        iter_src_files = super(ClearCaseSync, self).iter_src_files
        for rel_dir, files in iter_src_files():
            if fnmatch(rel_dir, "lost+found"):
                continue
            yield rel_dir, filter(lambda f: under_vc(rel_dir, f), files)

    def collect_private_files(self):
        command = "cleartool ls -recurse -view_only {}".format(self.src_root)

        return output_as_dict(command.split(' '))


def main(cache=False):
    validateCC()
    if cache:
        return syncCache()

    return ClearCaseSync(CC_DIR, cfg.getInclude()).do_sync()


def output_as_dict(args):
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    return dict((line.rstrip(), 1) for line in p.stdout)


def syncCache():
    cache1 = Cache(GIT_DIR)
    cache1.start()

    cache2 = Cache(GIT_DIR)
    cache2.initial()

    copied_file_count = 0
    for path in cache2.list():
        if not cache1.contains(path):
            cache1.update(path)
            if not os.path.isdir(os.path.join(CC_DIR, path.file)):
                if copy(path.file):
                    copied_file_count += 1
    cache1.write()
    return copied_file_count
