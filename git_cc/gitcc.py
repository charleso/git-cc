#!/usr/bin/env python
import inspect
import sys

from optparse import OptionParser

from . import checkin
from . import init
from . import rebase
from . import reset
from . import sync
from . import tag
from . import update
from . import version

commands = [
    init, rebase, checkin, sync, reset, tag, update, version
]


def main():
    args = sys.argv[1:]
    for cmd in commands:
        if args and get_module_name(cmd) == args[0]:
            return invoke(cmd, args)
    usage()


def invoke(cmd, args):
    _args, _, _, defaults = inspect.getargspec(cmd.main)
    defaults = defaults if defaults else []
    diff = len(_args) - len(defaults)
    _args = _args[diff:]
    parser = OptionParser(description=cmd.__doc__)
    for (name, default) in zip(_args, defaults):
        option = {
            'default': default,
            'help': cmd.ARGS[name],
            'dest': name,
        }
        if default is False:
            option['action'] = "store_true"
        elif default is None:
            option['action'] = "store"
        name = name.replace('_', '-')
        parser.add_option('--' + name, **option)
    (options, args) = parser.parse_args(args[1:])
    if len(args) < diff:
        parser.error("incorrect number of arguments")
    for name in _args:
        args.append(getattr(options, name))
    cmd.main(*args)


def usage():
    print('usage: gitcc COMMAND [ARGS]\n')
    width = 11
    for cmd in commands:
        print('    %s %s' % (get_module_name(cmd).ljust(width),
                             cmd.__doc__.split('\n')[0]))
    sys.exit(2)


def get_module_name(module):
    """Return the name of the given module, without the package name.

    For example, if the given module is checkin, the module name is
    "git_cc.checkin" and without the package name is "checkin".

    Note that the given module should already have been imported.

    """
    _, _, module_name = module.__name__.rpartition('.')
    return module_name

if __name__ == '__main__':
    main()
