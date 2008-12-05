from __init__ import *
import checkin, common
import unittest
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
        types = {'M': MockModfy}
        for type, file in files:
            types[type](self.expectedExec, commit, message, file)
        self.expectedExec.extend([\
            (['git', 'tag', '-f', CC_TAG, commit], ''), \
        ])
        self.commits.extend([commit, message, ''])
    def testEmpty(self):
        self.checkin()
    def testSimple(self):
        self.commit('sha1', 'commit1', [('M', 'rebase.py')])
        self.commit('sha2', 'commit2', [('M', 'rebase2.py')])
        self.checkin();

class MockModfy:
    def __init__(self, expectedExec, commit, message, file):
        hash1 = "hash1"
        hash2 = "hash2"
        blob = "blob"
        expectedExec.extend([\
            (['cleartool', 'co', '-reserved', '-nc', file], ''), \
            (['git', 'hash-object', join(CC_DIR, file)], hash1 + '\n'), \
            (['git', 'ls-tree', '-z', CC_TAG, file], '100644 blob %s %s' % (hash1, file)), \
            (['git', 'ls-tree', '-z', commit, file], '100644 blob %s %s' % (hash2, file)), \
            (['git', 'cat-file', 'blob', hash2], blob), \
            (join(CC_DIR, file), blob), \
            (['cleartool', 'ci', '-c', message, file], ''), \
        ])

if __name__ == "__main__":
    unittest.main()