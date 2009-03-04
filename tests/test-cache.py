import sys, shutil
sys.path.append("..")
from os.path import join
import unittest
import cache
from cache import Cache, CCFile
import tempfile

TEMP1 = """
file.py@@/main/a/b/1
"""

TEMP1_EXPECTED = """file.py@@/main/a/b/2
file2.py@@/main/c/2
"""

class CacheTest(unittest.TestCase):
    def testLoad(self):
        dir = tempfile.mkdtemp()
        f = open(join(dir, cache.FILE), 'w')
        f.write(TEMP1)
        f.close()
        try:
            c = Cache(dir)
            self.assertFalse(c.isChild(CCFile('file.py', '/main/a/1')))
            self.assertFalse(c.isChild(CCFile('file.py', r'\main\a\1')))
            self.assertTrue(c.isChild(CCFile('file.py', '/main/a/b/c/1')))
            self.assertFalse(c.isChild(CCFile('file.py', '/main/a/c/1')))
            c.update(CCFile('file.py', '/main/a/b/2'))
            c.update(CCFile('file2.py', '/main/c/2'))
            c.write()
            f = open(join(dir, cache.FILE), 'r')
            try:
                self.assertEqual(TEMP1_EXPECTED, f.read())
            finally:
                f.close()
        finally:
            shutil.rmtree(dir)

if __name__ == "__main__":
    unittest.main()
