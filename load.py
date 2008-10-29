import rebase

def load(args):
    rebase.loadHistory(open(args[0], 'r').read())
