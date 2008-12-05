from os.path import join, dirname, exists
import os, stat
from common import *
from datetime import datetime, timedelta
from users import users, mailSuffix
from fnmatch import fnmatch

"""
Things remaining:
1. Renames with no content change. Tricky.
"""

CC_LSH = ['lsh', '-fmt', '%o%m|%d|%u|%En|%Vn|%Nc\\n', '-recurse']
DELIM = '|'

def rebase(args):
    dryrun = '--dry-run' in args
    stash = '--stash' in args
    if not (dryrun or stash):
        checkPristine()
    since = getSince()
    history = getHistory(since)
    loadHistory(history, dryrun, stash)

def loadHistory(history, dryrun=False, stash=False):
    cs = parseHistory(history)
    cs.sort(lambda x, y: cmp(x.date, y.date))
    cs = mergeHistory(cs)
    if dryrun:
        return printGroups(cs)
    if not len(cs):
        return
    doStash(lambda: doCommit(cs), stash)

def doCommit(cs):
    id = git_exec(['log', '--pretty=format:%H', '-n', '1'])
    reset()
    try:
        commit(cs)
    finally:
        if len(id):
            reset(id)
            git_exec(['rebase', CC_TAG])

def getSince():
    date = git_exec(['log', '-n', '1', '--pretty=format:%ai', '%s^..%s' % (CC_TAG, CC_TAG)])
    if len(date) == 0:
        return cfg.get('since')
    date = date[:19]
    date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    date = date + timedelta(seconds=1)
    return datetime.strftime(date, '%d-%b-%Y.%H:%M:%S')

def getHistory(since):
    lsh = CC_LSH[:]
    if since:
        lsh.extend(['-since', since])
    lsh.extend(cfg.getList('include', '.'))
    return cc_exec(lsh)

def parseHistory(lines):
    changesets = []
    branches = cfg.getList('branches', 'main')
    def filterBranches(version):
        version = version.split('\\')
        version.pop()
        version = version[-1]
        for branch in branches:
            if fnmatch(version, branch):
                return True
        return False
    def add(split, comment):
        if not split:
            return
        cstype = split[0]
        if cstype in TYPES:
            cs = TYPES[cstype](split, comment)
            if filterBranches(cs.version) and cs.valid():
                changesets.append(cs)
    last = None
    comment = None
    for line in lines.splitlines():
        split = line.split(DELIM)
        if len(split) == 1 and last:
            comment += "\n" + split[0]
        else:
            add(last, comment)
            comment = split[5]
            last = split
    add(last, comment)
    return changesets

def mergeHistory(changesets):
    last = None
    groups = []
    def same(a, b):
        return a.subject == b.subject and a.user == b.user
    for cs in changesets:
        if last and same(last, cs):
            last.append(cs)
        else:
            last = Group(cs)
            groups.append(last)
    return groups

def commit(list):
    for cs in list:
        cs.commit()

def printGroups(groups):
    for cs in groups:
        print cs.user, '"%s"' % cs.subject
        for file in cs.files:
            print "  %s" % file.file

class Group:
    def __init__(self, cs):
        self.user = cs.user
        self.comment = cs.comment
        self.subject = cs.subject
        self.files = []
        self.append(cs)
    def append(self, cs):
        self.date = cs.date
        self.files.append(cs)
    def commit(self):
        def getUserEmail(user):
            return '<%s@%s>' % (user.lower().replace(' ','.').replace("'", ''), mailSuffix)
        for file in self.files:
            file.add()
        env = {}
        user = users[self.user]
        env['GIT_AUTHOR_DATE'] = env['GIT_COMMITTER_DATE'] = self.date
        env['GIT_AUTHOR_NAME'] = env['GIT_COMMITTER_NAME'] = user
        env['GIT_AUTHOR_EMAIL'] = env['GIT_COMMITTER_EMAIL'] = getUserEmail(user)
        comment = self.comment if self.comment.strip() != "" else "<empty message>"
        git_exec(['commit', '-m', comment], env=env)
        tag()

class Changeset(object):
    def __init__(self, split, comment):
        self.date = split[1]
        self.user = split[2]
        self.file = split[3]
        self.version = split[4]
        self.comment = comment
        self.subject = comment.split('\n')[0]
    def add(self):
        toFile = join(GIT_DIR, self.file)
        mkdirs(toFile)
        removeFile(toFile)
        cc_exec(['get','-to', toFile, self.file + "@@" + self.version])
        if not exists(toFile):
            git_exec(['checkout', 'HEAD', toFile])
        else:
            os.chmod(toFile, stat.S_IWRITE)
        git_exec(['add', self.file])
    def valid(self):
        return True

class Uncataloged(Changeset):
    def __init__(self, split, comment):
        super(Uncataloged, self).__init__(split, comment)
        self.removed = []
        for file in comment.split('\n'):
            if file.startswith('Uncataloged'):
                i = file.find('"')
                file = file[i+1:-2]
                file = join(self.file, file)
                if exists(join(GIT_DIR, file)):
                    self.removed.append(file)
    def add(self):
        for rm in self.removed:
            git_exec(['rm', rm])
    def valid(self):
        return len(self.removed) > 0

TYPES = {\
    'checkinversion': Changeset,\
    'checkindirectory version': Uncataloged,\
}