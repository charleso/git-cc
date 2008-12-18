"""Initialise gitcc with a clearcase directory"""

from common import *
from os import open
from os.path import join, exists

def main(ccdir):
    if not exists(join(GIT_DIR, '.git')):
        git_exec(['init'])
        git_exec(['config', 'core.autocrlf', 'false'])
        excludes = """*.class
*.jar
"""
        write(join(GIT_DIR, '.git', 'info', 'exclude'), excludes)
    cfg.set(CFG_CC, ccdir)
    cfg.write()
