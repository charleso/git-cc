from subprocess import Popen, PIPE
import imp
import os
import sys
from os.path import join, exists, abspath, dirname

# In which package module SafeConfigParser is available and under what name
# depends on the Python version
if sys.version_info[0] == 2:
    from ConfigParser import SafeConfigParser
elif sys.version_info[0] == 3 and sys.version_info[1] <= 2:
    from configparser import SafeConfigParser
else:
    from configparser import ConfigParser as SafeConfigParser

IS_CYGWIN = sys.platform == 'cygwin'

if IS_CYGWIN:
    FS = '\\'
else:
    FS = os.sep


class FakeUsersModule():

    def __init__(self):
        self.users = {}
        self.mailSuffix = ""


def get_users_module(path):
    """Load the module at the given path and return it.

    The path should point to a module that defines at its top-level a users
    dictionary ".users" and a mail suffix ".mailSuffix".

    If no file exists at the given path, this function returns an object with
    an empty dictionary for ".users" and the empty string for ".mailSuffix".

    """

    users_module = FakeUsersModule()
    if os.path.exists(path):
        users_module_path = os.path.join(path)
        users_module = imp.load_source("users", users_module_path)

    return users_module

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
    return popen('git', cmd, GIT_DIR, encoding='UTF-8', **args)

def cc_exec(cmd, **args):
    return popen('cleartool', cmd, CC_DIR, **args)

def popen(exe, cmd, cwd, env=None, decode=True, errors=True, encoding=None):
    cmd.insert(0, exe)
    if DEBUG:
        f = lambda a: a if not a.count(' ') else '"%s"' % a
        debug('> ' + ' '.join(map(f, cmd)))
    pipe = Popen(cmd, cwd=cwd, stdout=PIPE, stderr=PIPE, env=env)
    (stdout, stderr) = pipe.communicate()
    if encoding == None:
        encoding = ENCODING
    if errors and pipe.returncode > 0:
        raise Exception(decodeString(encoding, stderr + stdout))
    return stdout if not decode else decodeString(encoding, stdout)

def decodeString(encoding, encodestr):
    try:
        return encodestr.decode(encoding)
    except UnicodeDecodeError as e:
        print >> sys.stderr, encodestr, ":", e
        return encodestr.decode(encoding, "ignore")

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
    def __init__(self, branch, config_file=None):
        self.section = branch
        self.file = config_file
        if not self.file:
            self.file = join(GIT_DIR, '.git', 'gitcc')
        self.parser = SafeConfigParser()
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

    def getUsersModulePath(self):
        """Return the absolute path of the users module.

        In the configuration file, the path can be specified by an absolute
        path but also by a relative path. If it is a relative path, the path is
        taken relative to the directory that contains the configuration file.

        If the configuration file does not specify the path to the users
        module, this method returns the empty string.

        """
        abs_path = ''
        path = self.getCore('users_module_path')
        if path is not None:
            if os.path.isabs(path):
                abs_path = path
            else:
                config_dir = os.path.dirname(self.file)
                abs_path = os.path.join(config_dir, path)
        return abs_path

    def ignorePrivateFiles(self):
        """Return true if and only if private files should not be synced.

        If this option holds, only the files that are under ClearCase control
        will be synced. Otherwise all the files in the VOB are synced.

        """
        return self.getCore('ignore_private_files', False)


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
DEBUG = str(cfg.getCore('debug', True)) == str(True)
CC_TAG = CURRENT_BRANCH + '_cc'
CI_TAG = CURRENT_BRANCH + '_ci'
users = get_users_module(cfg.getUsersModulePath())
