"""Load history from snapshot file"""

import rebase

def main(args):
    rebase.loadHistory(open(args[0], 'r').read())
