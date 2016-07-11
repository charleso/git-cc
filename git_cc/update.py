"""Update the git repository with Clearcase manually, ignoring history"""

from __future__ import print_function

from .common import *
from . import reset
from . import sync


def main(message):
    cc_exec(['update', '.'], errors=False)
    if sync.main():
        git_exec(['add', '.'])
        git_exec(['commit', '-m', message])
        reset.main('HEAD')
    else:
        print("No files have changed, nothing to commit.")
