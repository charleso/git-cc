from os.path import join, exists

FILE = '.gitcc'

# TODO DIRTY?!?
class Cache(object):
    def __init__(self, dir):
        self.map = {}
        self.dir = dir
        self.empty = Version('/main/0')
        f = join(dir, FILE)
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
        self.read(cc_exec(['ls', '-recurse', '-short', cfg.getInclude()]))
    def read(self, lines):
        for line in lines.splitlines():
            if not line:
                continue
            self.update(CCFile2(line))
    def isChild(self, path):
        return self.map.get(path.file, self.empty).isChild(path.version)
    def update(self, path):
        self.map[path.file] = path.version
    def remove(self, file):
        del self.map[file]
    def write(self):
        lines = []
        keys = self.map.keys()
        keys.sort()
        for file in keys:
            lines.append(file + '@@' + self.map[file].version)
        f = open(join(self.dir, FILE), 'w')
        try:
            f.write('\n'.join(lines))
            f.write('\n')
        finally:
            f.close()

class CCFile(object):
    def __init__(self, file, version):
        self.file = file
        self.version = Version(version)

class CCFile2(CCFile):
    def __init__(self, line):
        [file, version] = line.split('@@')
        super(CCFile2, self).__init__(file, version)

class Version(object):
    def __init__(self, version):
        version = version.replace('\\', '/')
        self.version = version
    def isChild(self, version):
        return self.parent(version.version).startswith(self.parent(self.version))
    def parent(self, version):
        return '/'.join(version.split('/')[0:-1])
