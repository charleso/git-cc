"""Rebase from Clearcase"""

from os.path import join, dirname, exists, isdir
import os, stat
from .common import *
from datetime import datetime, timedelta
from fnmatch import fnmatch
from .clearcase import cc
from .cache import getCache, CCFile
from re import search

"""
Things remaining:
1. Renames with no content change. Tricky.
"""

CC_LSH = ['lsh', '-fmt', '%o%m|%Nd|%u|%En|%Vn|'+cc.getCommentFmt()+'\\n', '-recurse']
DELIM = '|'

ARGS = {
    'stash': 'Wraps the rebase in a stash to avoid file changes being lost',
    'dry_run': 'Prints a list of changesets to be imported',
    'lshistory': 'Prints the raw output of lshistory to be cached for load',
    'load': 'Loads the contents of a previously saved lshistory file',
}

cache = getCache()

def main(stash=False, dry_run=False, lshistory=False, load=None):
    validateCC()
    if not (stash or dry_run or lshistory):
        checkPristine()

    cc_exec(["update"], errors=False)

    since = getSince()
    cache.start()
    if load:
        history = open(load, 'r').read().decode(ENCODING)
    else:
        cc.rebase()
        history = getHistory(since)
        write(join(GIT_DIR, '.git', 'lshistory.bak'), history.encode(ENCODING))
    if lshistory:
        print(history)
    else:
        cs = parseHistory(history)
        cs = reversed(cs)
        cs = mergeHistory(cs)
        if dry_run:
            return printGroups(cs)
        if not len(cs):
            return
        doStash(lambda: doCommit(cs), stash)

def checkPristine():
    if(len(git_exec(['ls-files', '--modified']).splitlines()) > 0):
        fail('There are uncommitted files in your git directory')

def doCommit(cs):
    branch = getCurrentBranch()
    if branch:
        git_exec(['checkout', CC_TAG])
    try:
        commit(cs)
    finally:
        if branch:
            git_exec(['rebase', CI_TAG, CC_TAG])
            git_exec(['rebase', CC_TAG, branch])
        else:
            git_exec(['branch', '-f', CC_TAG])
        tag(CI_TAG, CC_TAG)

def getSince():
    try:
        date = git_exec(['log', '-n', '1', '--pretty=format:%ai', '%s' % CC_TAG])
        date = date[:19]
        date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        date = date + timedelta(seconds=1)
        return datetime.strftime(date, '%d-%b-%Y.%H:%M:%S')
    except:
        return cfg.get('since')

def getHistory(since):
    lsh = CC_LSH[:]
    if since:
        lsh.extend(['-since', since])
    lsh.extend(cfg.getInclude())
    return cc_exec(lsh)

def filterBranches(version, all=False):
    version = version.split(FS)
    version.pop()
    version = version[-1]
    branches = cfg.getBranches();
    if all:
        branches.extend(cfg.getExtraBranches())
    for branch in branches:
        if fnmatch(version, branch):
            return True
    return False

def parseHistory(lines):
    changesets = []
    def add(split, comment):
        if not split:
            return
        cstype = split[0]
        if cstype in TYPES:
            cs = TYPES[cstype](split, comment)
            try:
                if filterBranches(cs.version):
                    changesets.append(cs)
            except Exception as e:
                print('Bad line', split, comment)
                raise
    last = None
    comment = None
    for line in lines.splitlines():
        split = line.split(DELIM)
        if len(split) < 6 and last:
            # Cope with comments with '|' character in them
            comment += "\n" + DELIM.join(split)
        else:
            add(last, comment)
            comment = DELIM.join(split[5:])
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
    for group in groups:
        group.fixComment()
    return groups

def commit(list):
    for cs in list:
        cs.commit()

def printGroups(groups):
    for cs in groups:
        print('%s "%s"' % (cs.user, cs.subject))
        for file in cs.files:
            print("  %s" % file.file)

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
    def fixComment(self):
        self.comment = cc.getRealComment(self.comment)
        self.subject = self.comment.split('\n')[0]
    def commit(self):
        def getCommitDate(date):
            return date[:4] + '-' + date[4:6] + '-' + date[6:8] + ' ' + \
                   date[9:11] + ':' + date[11:13] + ':' + date[13:15]
        def getUserName(user):
            return str(user).split(' <')[0]
        def getUserEmail(user):
            email = search('<.*@.*>', str(user))
            if email == None:
                return '<%s@%s>' % (user.lower().replace(' ','.').replace("'", ''), users.mailSuffix)
            else:
                return email.group(0)
        files = []
        for file in self.files:
            files.append(file.file)
        for file in self.files:
            file.add(files)
        cache.write()
        env = os.environ
        user = users.users.get(self.user, self.user)
        env['GIT_AUTHOR_DATE'] = env['GIT_COMMITTER_DATE'] = str(getCommitDate(self.date))
        env['GIT_AUTHOR_NAME'] = env['GIT_COMMITTER_NAME'] = getUserName(user)
        env['GIT_AUTHOR_EMAIL'] = env['GIT_COMMITTER_EMAIL'] = str(getUserEmail(user))
        comment = self.comment if self.comment.strip() != "" else "<empty message>"
        try:
            git_exec(['commit', '-m', comment.encode(ENCODING)], env=env)
        except Exception as e:
            if search('nothing( added)? to commit', e.args[0]) == None:
                raise

def cc_file(file, version):
    return '%s@@%s' % (file, version)

class Changeset(object):
    def __init__(self, split, comment):
        self.date = split[1]
        self.user = split[2]
        self.file = split[3]
        self.version = split[4]
        self.comment = comment
        self.subject = comment.split('\n')[0]
    def add(self, files):
        self._add(self.file, self.version)
    def _add(self, file, version):
        if not cache.update(CCFile(file, version)):
            return
        if [e for e in cfg.getExclude() if fnmatch(file, e)]:
            return
        toFile = path(join(GIT_DIR, file))
        mkdirs(toFile)
        removeFile(toFile)
        try:
            cc_exec(['get','-to', toFile, cc_file(file, version)])
        except:
            if len(file) < 200:
                raise
            debug("Ignoring %s as it may be related to https://github.com/charleso/git-cc/issues/9" % file)
        if not exists(toFile):
            git_exec(['checkout', 'HEAD', toFile])
        else:
            os.chmod(toFile, os.stat(toFile).st_mode | stat.S_IWRITE)
        git_exec(['add', '-f', file], errors=False)

class Uncataloged(Changeset):
    def add(self, files):
        dir = path(cc_file(self.file, self.version))
        diff = cc_exec(['diff', '-diff_format', '-pred', dir], errors=False)
        def getFile(line):
            return join(self.file, line[2:max(line.find('  '), line.find(FS + ' '))])
        for line in diff.split('\n'):
            sym = line.find(' -> ')
            if sym >= 0:
                continue
            if line.startswith('<'):
                git_exec(['rm', '-r', getFile(line)], errors=False)
                cache.remove(getFile(line))
            elif line.startswith('>'):
                added = getFile(line)
                cc_added = join(CC_DIR, added)
                if not exists(cc_added) or isdir(cc_added) or added in files:
                    continue
                history = cc_exec(['lshistory', '-fmt', '%o%m|%Nd|%Vn\\n', added], errors=False)
                if not history:
                    continue
                history = filter(None, history.split('\n'))
                all_versions = self.parse_history(history)

                date = cc_exec(['describe', '-fmt', '%Nd', dir])
                actual_versions = self.filter_versions(all_versions, lambda x: x[1] < date)

                versions = self.checkin_versions(actual_versions)
                if not versions:
                    print("It appears that you may be missing a branch in the includes section of your gitcc config for file '%s'." % added)
                    continue
                self._add(added, versions[0][2].strip())

    def checkin_versions(self, versions):
        return self.filter_versions_by_type(versions, 'checkinversion')

    def filter_versions_by_type(self, versions, type):
        def f(s):
            return s[0] == type and filterBranches(s[2], True)
        return self.filter_versions(versions, f)

    def filter_versions(self, versions, handler):
        return list(filter(handler, versions))

    def parse_history(self, history_arr):
        return list(map(lambda x: x.split('|'), history_arr))


TYPES = {\
    'checkinversion': Changeset,\
    'checkindirectory version': Uncataloged,\
}
