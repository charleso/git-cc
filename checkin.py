"""Checkin new git changesets to Clearcase"""

from common import *
from clearcase import cc
from status import Modify, Add, Delete, Rename
import filecmp
from os import listdir
from os.path import isdir
import cache

IGNORE_CONFLICTS=False

ARGS = {
    'force': 'ignore conflicts and check-in anyway',
    'no_deliver': 'do not deliver in UCM mode',
}

def main(force=False, no_deliver=False):
    validateCC()
    global IGNORE_CONFLICTS
    if force:
        IGNORE_CONFLICTS=True
    cc_exec(['update', '.'], errors=False)
    log = git_exec(['log', '--first-parent', '--reverse', '--pretty=format:%x00%n%H%n%s%n%n%b', CI_TAG + '..'])
    if not log:
        return
    cc.rebase()
    comment = []
    id = None
    def _commit():
        if not id:
            return
        statuses = getStatuses(id)
        checkout(statuses, '\n'.join(comment).strip())
        tag(CI_TAG, id)
    for line in log.splitlines():
        if line == "\x00":
            _commit()
            comment = []
            id = None
        elif not id:
            id = line
        else:
            comment.append(line)
    _commit()
    if not no_deliver:
        cc.commit()

def getStatuses(id):
    status = git_exec(['diff','--name-status', '-M', '-z', '--ignore-submodules', '%s^..%s' % (id, id)])
    types = {'M':Modify, 'R':Rename, 'D':Delete, 'A':Add, 'C':Add}
    list = []
    split = status.split('\x00')
    while len(split) > 1:
        char = split.pop(0)[0] # first char
        args = [split.pop(0)]
        if char == 'R':
            args.append(split.pop(0))
        elif char == 'C':
            args = [split.pop(0)]
        if args[0] == cache.FILE:
            continue
        type = types[char](args)
        type.id = id
        list.append(type)
    return list

def checkout(stats, comment):
    """Poor mans two-phase commit"""
    failed = None
    transaction = Transaction(comment)
    for stat in stats:
        try:
            stat.stage(transaction)
        except:
            failed = True
            break;
    if failed:
        transaction.rollback()
        raise
    for stat in stats:
         stat.commit(transaction)
    transaction.commit(comment);

class Transaction:
    def __init__(self, comment):
        self.checkedout = []
        cc.mkact(comment)
        self.base = git_exec(['merge-base', CI_TAG, 'HEAD']).strip()
    def add(self, file):
        self.checkedout.append(file)
    def co(self, file):
        cc_exec(['co', '-reserved', '-nc', file])
        self.add(file)
    def stageDir(self, file):
        file = file if file else '.'
        if file not in self.checkedout:
            self.co(file)
    def stage(self, file):
        global IGNORE_CONFLICTS    
        self.co(file)
        ccid = git_exec(['hash-object', join(CC_DIR, file)])[0:-1]
        gitid = getBlob(self.base, file)
        if ccid != gitid:
            if not IGNORE_CONFLICTS:
                raise Exception('File has been modified: %s. Try rebasing.' % file)
            else:
                print ('WARNING: Detected possible confilct with',file,'...ignoring...')
    def rollback(self):
        for file in self.checkedout:
            cc_exec(['unco', '-rm', file])
        cc.rmactivity()
    def commit(self, comment):
        for file in self.checkedout:
            cc_exec(['ci', '-identical', '-c', comment, file])
