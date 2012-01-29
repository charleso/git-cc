from distutils import __version__
v30 = __version__.find("3.") == 0

from subprocess import Popen, PIPE
import os, sys
from os.path import join, exists, abspath, dirname
if v30:
    from configparser import SafeConfigParser
else:
    from ConfigParser import SafeConfigParser

IS_CYGWIN = sys.platform == 'cygwin'

if IS_CYGWIN:
    FS = '\\'
else:
    FS = os.sep

CFG_CC = 'clearcase'
CC_DIR = None
ENCODING = None
if hasattr(sys.stdin, 'encoding'):
    ENCODING = sys.stdin.encoding
if ENCODING is None:
    import locale
    locale_name, ENCODING = locale.getdefaultlocale()
if ENCODING is None:
    ENCODING = "ISO8859-1"
DEBUG = False

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

def git_exec(cmd, **args):
    return popen('git', cmd, GIT_DIR, **args)

def cc_exec(cmd, **args):
    return popen('cleartool', cmd, CC_DIR, **args)

def popen(exe, cmd, cwd, env=None, decode=True, errors=True):
    cmd.insert(0, exe)
    if DEBUG:
        f = lambda a: a if not a.count(' ') else '"%s"' % a
        debug('> ' + ' '.join(map(f, cmd)))
    pipe = Popen(cmd, cwd=cwd, stdout=PIPE, stderr=PIPE, env=env)
    (stdout, stderr) = pipe.communicate()
    if errors and pipe.returncode > 0:
        raise Exception((stderr + stdout).decode(ENCODING))
    return stdout if not decode else stdout.decode(ENCODING)

def tag(tag, id="HEAD"):
    git_exec(['tag', '-f', tag, id])

def reset(tag=None):
    git_exec(['reset', '--hard', tag or CC_TAG])

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

def getCurrentBranch():
    for branch in git_exec(['branch']).split('\n'):
        if branch.startswith('*'):
            branch = branch[2:]
            if branch == '(no branch)':
                fail("Why aren't you on a branch?")
            return branch
    return ""

class GitConfigParser():
    CORE = 'core'
    def __init__(self, branch):
        self.section = branch
        self.file = join(GIT_DIR, '.git', 'gitcc')
        self.parser = SafeConfigParser();
        self.parser.add_section(self.section)
    def set(self, name, value):
        self.parser.set(self.section, name, value)
    def read(self):
        self.parser.read(self.file)
    def write(self):
        self.parser.write(open(self.file, 'w'))
    def getCore(self, name, *args):
        return self._get(self.CORE, name, *args)
    def get(self, name, *args):
        return self._get(self.section, name, *args)
    def _get(self, section, name, default=None):
        if not self.parser.has_option(section, name):
            return default
        return self.parser.get(section, name)
    def getList(self, name, default=None):
        return self.get(name, default).split('|')
    def getInclude(self):
        return self.getCore('include', '.').split('|')
    def getExclude(self):
        return self.getCore('exclude', '.').split('|')
    def getBranches(self):
        return self.getList('branches', 'main')
    def getExtraBranches(self):
        return self.getList('_branches', 'main')

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

def validateCC():
    if not CC_DIR:
        fail("No 'clearcase' variable found for branch '%s'" % CURRENT_BRANCH)
        
def path(path, args='-m'):
    if IS_CYGWIN:
        return os.popen('cygpath %s "%s"' %(args, path)).readlines()[0].strip()
    else:
        return path

GIT_DIR = path(gitDir())
if not exists(join(GIT_DIR, '.git')):
    fail("fatal: Not a git repository (or any of the parent directories): .git")
CURRENT_BRANCH = getCurrentBranch() or 'master'
cfg = GitConfigParser(CURRENT_BRANCH)
cfg.read()
CC_DIR = path(cfg.get(CFG_CC))
DEBUG = cfg.getCore('debug', True)
CC_TAG = CURRENT_BRANCH + '_cc'
CI_TAG = CURRENT_BRANCH + '_ci'

