"""Checkin new git changesets to Clearcase"""

from common import *
from clearcase import cc
from status import Modify, Add, Delete, Rename
import filecmp
from os import listdir
from os.path import isdir

def main():
    cc_exec(['update', '.'])
    log = git_exec(['log', '--reverse', '--pretty=format:%H%n%s%n%b', CI_TAG + '..'])
    comment = []
    id = None
    def _commit():
        if not id:
            return
        statuses = getStatuses(id)
        checkout(statuses, '\n'.join(comment))
        tag(CI_TAG, id)
    for line in log.splitlines():
        if line == "":
            _commit()
            comment = []
            id = None
        if not id:
            id = line
        else:
            comment.append(line)
    _commit()

def getStatuses(id):
    status = git_exec(['diff','--name-status', '-M', '-z', '%s^..%s' % (id, id)])
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
        self.co(file)
        ccid = git_exec(['hash-object', join(CC_DIR, file)])[0:-1]
        gitid = getBlob(git_exec(['merge-base', CI_TAG, 'HEAD']).strip(), file)
        if ccid != gitid:
            raise Exception('File has been modified: %s. Try rebasing.' % file)
    def rollback(self):
        for file in self.checkedout:
            cc_exec(['unco', '-rm', file])
        cc.rmactivity()
    def commit(self, comment):
        for file in self.checkedout:
            cc_exec(['ci', '-identical', '-c', comment, file])
        cc.commit()
