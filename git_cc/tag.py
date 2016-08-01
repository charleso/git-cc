"""Tag a particular commit as gitcc start point"""

from .common import *

def main(commit):
    tag(CI_TAG, commit)
