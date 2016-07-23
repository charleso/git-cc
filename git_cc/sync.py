"""Copy files from Clearcase to Git manually"""

import filecmp
import subprocess

from .common import *
from .cache import *
import os, shutil, stat
from os.path import join, abspath, isdir
from fnmatch import fnmatch

ARGS = {
    'cache': 'Use the cache for faster syncing'
}

class Filters(object):
    """Implements a list of filter functions.

    A filter function returns True or False on a given directory or file. True
    means that the directory (or file) should be skipped and False means it
    should not be skipped.

    If and only if at least one of a filter functions returns True for a given
    directory (or file), that directory (or file) should be skipped.

    """

    def __init__(self, *filters):

        self.filters = [f for f in filters]

    def skip(self, path):
        skip_path = False
        for f in self.filters:
            skip_path = f(path)
            if skip_path:
                break
        return skip_path


class Sync(object):
    """Implements the copying of a directory tree."""

    def __init__(self, src_root, dst_root):
        self.src_root = os.path.abspath(src_root)
        self.dst_root = os.path.abspath(dst_root)

    def do_sync(self):
        copied_file_count = 0
        for rel_dir, file_names in self.iter_src_files():
            for file_name in file_names:
                file_path = join(rel_dir, file_name)
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

    def __init__(self, src_root, dst_root):
        super(ClearCaseSync, self). __init__(src_root, dst_root)

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
        return output_as_dict(["blablabla"])


def main(cache=False):
    validateCC()
    if cache:
        return syncCache()

    return ClearCaseSync(CC_DIR, cfg.getInclude()).do_sync()


def copy(file, src_dir, dst_dir):
    src_file = join(src_dir, file)
    dst_file = join(dst_dir, file)
    skip_file = os.path.exists(dst_file) and \
        filecmp.cmp(src_file, dst_file, shallow=False)
    if not skip_file:
        debug('Copying to %s' % dst_file)
        mkdirs(dst_file)
        shutil.copy2(src_file, dst_file)
        os.chmod(dst_file, stat.S_IREAD | stat.S_IWRITE)
        return True
    return False


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
            if not isdir(join(CC_DIR, path.file)):
                if copy(path.file):
                    copied_file_count += 1
    cache1.write()
    return copied_file_count
