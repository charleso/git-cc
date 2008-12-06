from __init__ import *
import checkin, common
import unittest, os
from os.path import join, abspath
from common import CC_DIR, CC_TAG

class CheckinTest(TestCaseEx):
    def setUp(self):
        TestCaseEx.setUp(self)
        self.expectedExec.append((['cleartool', 'update', '.'], ''))
        self.commits = []
    def checkin(self):
        self.expectedExec.insert(1, \
            (['git', 'log', '--reverse', '--pretty=format:%H%n%s%n%b', '%s..' % CC_TAG], '\n'.join(self.commits)), \
        )
        checkin.checkin([])
        self.assert_(not len(self.expectedExec))
    def commit(self, commit, message, files):
        nameStatus = []
        for type, file in files:
            nameStatus.append('%s\0%s' % (type, file))
        self.expectedExec.extend([\
            (['git', 'diff', '--name-status', '-M', '-z', '%s^..%s' % (commit, commit)], '\n'.join(nameStatus)), \
        ])
        types = {'M': MockModfy, 'A': MockAdd, 'D': MockDelete}
        for type, file in files:
            types[type](self.expectedExec, commit, message, file)
        self.expectedExec.extend([\
            (['git', 'tag', '-f', CC_TAG, commit], ''), \
        ])
        self.commits.extend([commit, message, ''])
    def testEmpty(self):
        self.checkin()
    def testSimple(self):
        self.commit('sha1', 'commit1', [('M', 'a.py')])
        self.commit('sha2', 'commit2', [('M', 'b.py')])
        self.commit('sha3', 'commit3', [('A', 'c.py')])
        self.checkin();
    def testFolderAdd(self):
        self.commit('sha4', 'commit4', [('A', 'a/b/c/d.py')])
        self.checkin();
    def testDelete(self):
        os.mkdir(join(CC_DIR, 'd'))
        self.commit('sha4', 'commit4', [('D', 'd/e.py')])
        self.checkin();

class MockStatus:
    def lsTree(self, id, file, hash):
        return (['git', 'ls-tree', '-z', id, file], '100644 blob %s %s' % (hash, file))
    def catFile(self, file, hash):
        blob = "blob"
        return [\
            (['git', 'cat-file', 'blob', hash], blob), \
            (join(CC_DIR, file), blob), \
        ]
    def co(self, file):
        return (['cleartool', 'co', '-reserved', '-nc', file], '')
    def ci(self, message, file):
        return (['cleartool', 'ci', '-c', message, file], '')

class MockModfy(MockStatus):
    def __init__(self, expectedExec, commit, message, file):
        hash1 = "hash1"
        hash2 = "hash2"
        expectedExec.extend([\
            self.co(file), \
            (['git', 'hash-object', join(CC_DIR, file)], hash1 + '\n'), \
            self.lsTree(CC_TAG, file, hash1), \
            self.lsTree(commit, file, hash2), \
        ])
        expectedExec.extend(self.catFile(file, hash2))
        expectedExec.append((['cleartool', 'ci', '-c', message, file], ''))

class MockAdd(MockStatus):
    def __init__(self, e, commit, message, file):
        hash = 'hash'
        files = []
        files.append(CC_DIR)
        e.append(self.co(CC_DIR))
        path = ""
        for f in file.split('/')[0:-1]:
            path = path + f + '/'
            f = join(CC_DIR, path[0:-1])
            files.append(f)
            e.append((['cleartool', 'mkelem', '-nc', '-eltype', 'directory', abspath(f)], ''))
        e.append(self.lsTree(commit, file, hash))
        e.extend(self.catFile(file, hash))
        e.append((['cleartool', 'mkelem', '-nc', file], ''))
        for f in files:
            e.append(self.ci(message, f))
        e.append(self.ci(message, file))

class MockDelete(MockStatus):
    def __init__(self, e, commit, message, file):
        dir = file[0:file.rfind('/')]
        e.extend([\
            self.co(dir), \
            (['cleartool', 'rm', file], ''), \
            self.ci(message, dir), \
        ])

if __name__ == "__main__":
    unittest.main()