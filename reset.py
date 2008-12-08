from common import *

def reset(args):
    git_exec(['reset', '--hard', args[0]])
    git_exec(['branch', '-f', CC_TAG])
    tag(CI_TAG)
