"""Reset hard to a specific changeset"""

from .common import *

def main(commit):
    git_exec(['branch', '-f', CC_TAG, commit])
    tag(CI_TAG, commit)
