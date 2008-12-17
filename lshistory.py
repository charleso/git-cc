import rebase

def main(args):
    print rebase.getHistory(args[0] if len(args) else rebase.getSince())
