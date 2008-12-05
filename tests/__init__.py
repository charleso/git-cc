import sys
sys.path.append("..")
import common
import unittest

common.CC_DIR = "/tmp"

class TestCaseEx(unittest.TestCase):
    def setUp(self):
        self.expectedExec = []
        def check(actual):
            self.assert_(len(self.expectedExec), actual)
            expected, out = self.expectedExec.pop(0)
            self.assertEquals(expected, actual)
            return out
        def mockPopen(exe, cmd, cwd, env=None):
            cmd.insert(0, exe)
            return check(cmd)
        def mockWrite(file, blob):
            self.assertEquals(check(file), blob)
        common.popen = mockPopen
        common._write = mockWrite

