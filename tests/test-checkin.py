from __init__ import *
import checkin, common
import unittest, os
from os.path import join
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
        types = {'M': MockModfy, 'A': MockAdd}
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
    def __init__(self, expectedExec, commit, message, file):
        hash = 'hash'
        expectedExec.extend([\
            self.co(CC_DIR), \
            self.lsTree(commit, file, hash), \
        ])
        expectedExec.extend(self.catFile(file, hash))
        expectedExec.extend([\
            (['cleartool', 'mkelem', '-nc', file], ''), \
            self.ci(message, CC_DIR), \
            self.ci(message, file), \
        ])

if __name__ == "__main__":
    unittest.main()