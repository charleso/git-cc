"""Update the git repository with Clearcase manually, ignoring history"""

from common import *
import sync, reset

def main(message):
    cc_exec(['update', '.'], errors=False)
    sync.main()
    git_exec(['add', '.'])
    git_exec(['commit', '-m', message])
    reset.main('HEAD')
