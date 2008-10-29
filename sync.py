from common import *
import os, shutil
from os.path import join, abspath
from fnmatch import fnmatch

def sync(args):
    base = abspath(CC_DIR)
    for (dirpath, dirnames, filenames) in os.walk(CC_DIR):
        reldir = dirpath[len(base)+1:]
        for file in filenames:
            if fnmatch(file, '*.jar'):
                newFile = join(GIT_DIR, reldir, file)
                debug('Copying %s' % newFile)
                mkdirs(newFile)
                shutil.copy(join(dirpath, file), newFile)