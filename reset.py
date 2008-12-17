"""Reset hard to a specific changeset"""

from common import *

def main(args):
    git_exec(['reset', '--hard', args[0]])
    git_exec(['branch', '-f', CC_TAG])
    tag(CI_TAG)
