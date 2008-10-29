import rebase

def lshistory(args):
    print rebase.getHistory(args[0] if len(args) else rebase.getSince())
