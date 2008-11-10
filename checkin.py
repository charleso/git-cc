from common import *
from status import Modify, Add, Delete, Rename
import filecmp
from os import listdir
from os.path import isdir, abspath

def checkin(args):
    cc_exec(['update', '.'])
    log = git_exec(['log', '--reverse', '--pretty=format:%H%n%s%n%b', CC_TAG + '..'])
    comment = []
    id = None
    def _commit():
        if not id:
            return
        statuses = getStatuses(id)
        checkout(statuses, '\n'.join(comment))
        # TODO We need to do something clever with the time stamp
        tag(id)
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
    types = {'M':Modify, 'R':Rename, 'D':Delete, 'A':Add}
    list = []
    split = status.split('\x00')
    while len(split) > 1:
        char = split.pop(0)[0] # first char
        args = [split.pop(0)]
        if char == 'R':
            args.append(split.pop(0))
        type = types[char](args)
        type.id = id
        list.append(type)
    return list

def checkout(stats, comment):
    """Poor mans two-phase commit"""
    failed = None
    transaction = Transaction()
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
    def __init__(self):
        self.checkedout = []
    def _add(self, file):
        if file in self.checkedout:
            debug("File already staged %s" % file)
            return False
        self.checkedout.append(file)
        return True
    def stage(self, file):
        if not self._add(file):
            return
        cc_exec(['co', '-reserved', '-nc', file])
        if not isdir(join(CC_DIR, file)):
            ccid = git_exec(['hash-object', join(CC_DIR, file)])[0:-1]
            gitid = getBlob(CC_TAG, file)
            if ccid != gitid:
                raise Exception('File has been modified: %s. Try rebasing.' % file)
    def mkdirelem(self, file):
        cc_exec(['mkelem', '-nc', '-eltype', 'directory', abspath(file)])
        self._add(file)
    def mkelem(self, file):
        cc_exec(['mkelem', '-nc', file])
        self._add(file)
    def rollback(self):
        for file in self.checkedout:
            cc_exec(['unco', '-rm', file])
    def commit(self, comment):
        for file in self.checkedout:
            cc_exec(['ci', '-c', comment, file])
        # TODO self.rollback()
