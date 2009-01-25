from distutils import __version__
v30 = __version__.find("3.") == 0

from subprocess import Popen, PIPE
import os, sys
from os.path import join, exists, abspath, dirname
if v30:
    from configparser import SafeConfigParser
else:
    from ConfigParser import SafeConfigParser

CC_TAG = 'clearcase'
CI_TAG = 'clearcase_ci'
CFG_CC = 'clearcase'
CC_DIR = None

def fail(string):
    print(string)
    sys.exit(2)

def doStash(f, stash):
    if(stash):
        git_exec(['stash'])
    f()
    if(stash):
        git_exec(['stash', 'pop'])

def debug(string):
    if DEBUG:
        print(string)

def git_exec(cmd, env=None):
    return popen('git', cmd, GIT_DIR, env=env)

def cc_exec(cmd):
    return popen('cleartool', cmd, CC_DIR)

def popen(exe, cmd, cwd, env=None):
    cmd.insert(0, exe)
    if DEBUG:
        debug('> ' + ' '.join(cmd))
    input = Popen(cmd, cwd=cwd, stdout=PIPE, env=env).stdout.read()
    input = input.decode()
    return input if v30 else str(input)

def tag(tag, id="HEAD"):
    git_exec(['tag', '-f', tag, id])

def reset(tag=CC_TAG):
    git_exec(['reset', '--hard', tag])

def getBlob(sha, file):
    return git_exec(['ls-tree', '-z', sha, file]).split(' ')[2].split('\t')[0]

def gitDir():
    def findGitDir(dir):
        if not exists(dir) or dirname(dir) == dir:
            return '.'
        if exists(join(dir, '.git')):
            return dir
        return findGitDir(dirname(dir))
    return findGitDir(abspath('.'))

class GitConfigParser():
    section = 'gitcc'
    def __init__(self):
        self.file = join(GIT_DIR, '.git', 'gitcc')
        self.parser = SafeConfigParser();
        self.parser.add_section(self.section)
    def set(self, name, value):
        self.parser.set(self.section, name, value)
    def read(self):
        self.parser.read(self.file)
    def write(self):
        self.parser.write(open(self.file, 'w'))
    def get(self, name, default=None):
        if not self.parser.has_option(self.section, name):
            return default
        return self.parser.get(self.section, name)
    def getList(self, name, default=None):
        return self.get(name, default).split('|')

def checkPristine():
    if not CC_DIR:
        fail('No .git directory found')
    if(len(git_exec(['ls-files', '--modified']).splitlines()) > 0):
        fail('There are uncommitted files in your git directory')

def write(file, blob):
    _write(file, blob)

def _write(file, blob):
    f = open(file, 'wb')
    f.write(blob)
    f.close()

def mkdirs(file):
    dir = dirname(file)
    if not exists(dir):
        os.makedirs(dir)

def removeFile(file):
    if exists(file):
        os.remove(file)

GIT_DIR = gitDir()
cfg = GitConfigParser()
if exists(join(GIT_DIR, '.git')):
    cfg.read()
    CC_DIR = cfg.get(CFG_CC)
DEBUG = cfg.get('debug', True)
