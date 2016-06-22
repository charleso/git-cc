"""Copy files from Clearcase to Git manually"""

import filecmp

from common import *
from cache import *
import os, shutil, stat
from os.path import join, abspath, isdir
from fnmatch import fnmatch

ARGS = {
    'cache': 'Use the cache for faster syncing'
}

def main(cache=False):
    validateCC()
    if cache:
        return syncCache()
    glob = '*'
    base = abspath(CC_DIR)
    copied_file_count = 0
    for i in cfg.getInclude():
        for (dirpath, dirnames, filenames) in os.walk(join(CC_DIR, i)):
            reldir = dirpath[len(base)+1:]
            if fnmatch(reldir, './lost+found'):
                continue
            for file in filenames:
                if fnmatch(file, glob):
                    if copy(join(reldir, file)):
                        copied_file_count += 1
    return copied_file_count


def copy(file, src_dir=CC_DIR, dst_dir=GIT_DIR):
    src_file = join(src_dir, file)
    dst_file = join(dst_dir, file)
    skip_file = os.path.exists(dst_file) and filecmp.cmp(src_file, dst_file)
    if not skip_file:
        debug('Copying to %s' % dst_file)
        mkdirs(dst_file)
        shutil.copy2(src_file, dst_file)
        os.chmod(dst_file, stat.S_IREAD | stat.S_IWRITE)
        return True
    return False

def syncCache():
    cache1 = Cache(GIT_DIR)
    cache1.start()

    cache2 = Cache(GIT_DIR)
    cache2.initial()

    for path in cache2.list():
        if not cache1.contains(path):
            cache1.update(path)
            if not isdir(join(CC_DIR, path.file)):
                copy(path.file)
    cache1.write()
