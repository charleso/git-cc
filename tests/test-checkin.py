from __init__ import *
import checkin, common
import unittest, os
from os.path import join
from common import CC_DIR, CI_TAG

class CheckinTest(TestCaseEx):
    def setUp(self):
        TestCaseEx.setUp(self)
        self.expectedExec.append((['cleartool', 'update', '.'], ''))
        self.commits = []
    def checkin(self):
        self.expectedExec.insert(1,
            (['git', 'log', '--first-parent', '--reverse', '--pretty=format:%H%n%s%n%b', '%s..' % CI_TAG], '\n'.join(self.commits)),
        )
        checkin.main()
        self.assert_(not len(self.expectedExec))
    def commit(self, commit, message, files):
        nameStatus = []
        for type, file in files:
            nameStatus.append('%s\0%s' % (type, file))
        self.expectedExec.extend([
            (['git', 'diff', '--name-status', '-M', '-z', '%s^..%s' % (commit, commit)], '\n'.join(nameStatus)),
        ])
        types = {'M': MockModfy, 'A': MockAdd, 'D': MockDelete, 'R': MockRename}
        self.expectedExec.extend([
            (['git', 'merge-base', CI_TAG, 'HEAD'], 'abcdef'),
        ])
        for type, file in files:
            types[type](self.expectedExec, commit, message, file)
        self.expectedExec.extend([
            (['git', 'tag', '-f', CI_TAG, commit], ''),
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
    def testRename(self):
        os.mkdir(join(CC_DIR, 'a'))
        self.commit('sha1', 'commit1', [('R', 'a/b.py\0c/d.py')])
        self.checkin();

class MockStatus:
    def lsTree(self, id, file, hash):
        return (['git', 'ls-tree', '-z', id, file], '100644 blob %s %s' % (hash, file))
    def catFile(self, file, hash):
        blob = "blob"
        return [
            (['git', 'cat-file', 'blob', hash], blob),
            (join(CC_DIR, file), blob),
        ]
    def hash(self, file):
        hash1 = 'hash1'
        return [
            (['git', 'hash-object', join(CC_DIR, file)], hash1 + '\n'),
            self.lsTree('abcdef', file, hash1),
        ]
    def co(self, file):
        return (['cleartool', 'co', '-reserved', '-nc', file], '')
    def ci(self, message, file):
        return (['cleartool', 'ci', '-identical', '-c', message, file], '')
    def mkelem(self, file):
        return (['cleartool', 'mkelem', '-nc', '-eltype', 'directory', file], '')
    def dir(self, file):
        return file[0:file.rfind('/')];

class MockModfy(MockStatus):
    def __init__(self, e, commit, message, file):
        hash2 = "hash2"
        e.append(self.co(file))
        e.extend(self.hash(file))
        e.append(self.lsTree(commit, file, hash2))
        e.extend(self.catFile(file, hash2))
        e.append(self.ci(message, file))

class MockAdd(MockStatus):
    def __init__(self, e, commit, message, file):
        hash = 'hash'
        files = []
        files.append(".")
        e.append(self.co("."))
        path = ""
        for f in file.split('/')[0:-1]:
            path = path + f + '/'
            f = path[0:-1]
            files.append(f)
            e.append(self.mkelem(f))
        e.append(self.lsTree(commit, file, hash))
        e.extend(self.catFile(file, hash))
        e.append((['cleartool', 'mkelem', '-nc', file], '.'))
        for f in files:
            e.append(self.ci(message, f))
        e.append(self.ci(message, file))

class MockDelete(MockStatus):
    def __init__(self, e, commit, message, file):
        dir = file[0:file.rfind('/')]
        e.extend([
            self.co(dir),
            (['cleartool', 'rm', file], ''),
            self.ci(message, dir),
        ])

class MockRename(MockStatus):
    def __init__(self, e, commit, message, file):
        a, b = file.split('\0')
        hash = 'hash'
        e.extend([
            self.co(self.dir(a)),
            self.co(a),
        ])
        e.extend(self.hash(a))
        e.extend([
            self.co("."),
            self.mkelem(self.dir(b)),
            (['cleartool', 'mv', '-nc', a, b], '.'),
            self.lsTree(commit, b, hash),
        ])
        e.extend(self.catFile(b, hash))
        e.extend([
            self.ci(message, self.dir(a)),
            self.ci(message, "."),
            self.ci(message, self.dir(b)),
            self.ci(message, b),
        ])

if __name__ == "__main__":
    unittest.main()
