"""Reset hard to a specific changeset"""

from common import *

def main(commit):
    git_exec(['reset', '--hard', commit])
    git_exec(['branch', '-f', CC_TAG])
    tag(CI_TAG)
