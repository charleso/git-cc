"""Copy files from Clearcase to Git manually"""

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
    for i in cfg.getInclude():
        for (dirpath, dirnames, filenames) in os.walk(join(CC_DIR, i)):
            reldir = dirpath[len(base)+1:]
            if fnmatch(reldir, './lost+found'):
                continue
            for file in filenames:
                if fnmatch(file, glob):
                    copy(join(reldir, file))

def copy(file):
    newFile = join(GIT_DIR, file)
    debug('Copying %s' % newFile)
    mkdirs(newFile)
    shutil.copy(join(CC_DIR, file), newFile)
    os.chmod(newFile, stat.S_IREAD | stat.S_IWRITE)

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
