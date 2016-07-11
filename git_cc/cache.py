from os.path import join, exists
from .common import *

FILE = '.gitcc'

def getCache():
    if cfg.getCore('cache', True) == 'False':
        return NoCache()
    return Cache(GIT_DIR)

class Cache(object):
    def __init__(self, dir):
        self.map = {}
        self.file = FILE
        self.dir = dir
        self.empty = Version('/main/0')
    def start(self):
        f = join(self.dir, self.file)
        if exists(f):
            self.load(f)
        else:
            self.initial()
    def load(self, file):
        f = open(file, 'r')
        try:
            self.read(f.read())
        finally:
            f.close()
    def initial(self):
        ls = ['ls', '-recurse', '-short']
        ls.extend(cfg.getInclude())
        self.read(cc_exec(ls))
    def read(self, lines):
        for line in lines.splitlines():
            if line.find('@@') < 0:
                continue
            self.update(CCFile2(line))
    def update(self, path):
        isChild = self.map.get(path.file, self.empty).isChild(path.version)
        if isChild:
            self.map[path.file] = path.version
        return isChild or path.version.endswith(cfg.getBranches()[0])
    def remove(self, file):
        if file in self.map:
            del self.map[file]
    def write(self):
        lines = []
        keys = self.map.keys()
        keys = sorted(keys)
        for file in keys:
            lines.append(file + '@@' + self.map[file].full)
        f = open(join(self.dir, self.file), 'w')
        try:
            f.write('\n'.join(lines))
            f.write('\n')
        finally:
            f.close()
        git_exec(['add', self.file])
    def list(self):
        values = []
        for file, version in self.map.items():
            values.append(CCFile(file, version.full))
        return values
    def contains(self, path):
        return self.map.get(path.file, self.empty).full == path.version.full

class NoCache(object):
    def start(self):
        pass
    def write(self):
        pass
    def update(self, path):
        return True
    def remove(self, file):
        pass

class CCFile(object):
    def __init__(self, file, version):
        if file.startswith('./') or file.startswith('.\\'):
            file = file[2:]
        self.file = file
        self.version = Version(version)

class CCFile2(CCFile):
    def __init__(self, line):
        [file, version] = line.rsplit('@@', 1)
        super(CCFile2, self).__init__(file, version)

class Version(object):
    def __init__(self, version):
        self.full = version.replace('\\', '/')
        self.version = '/'.join(self.full.split('/')[0:-1])
    def isChild(self, version):
        return version.version.startswith(self.version)
    def endswith(self, version):
        return self.version.endswith('/' + version)
