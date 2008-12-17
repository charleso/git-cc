from common import *
from os import open
from os.path import join, exists

def main(args):
    if not exists(join(GIT_DIR, '.git')):
        git_exec(['init'])
        excludes = """*.class
*.jar
"""
        write(join(GIT_DIR, '.git', 'info', 'exclude'), excludes)
    cfg.set(CFG_CC, args[0])
    cfg.write()
