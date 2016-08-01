# -*- coding: utf-8 -*-

import os
import re

from setuptools import setup, find_packages

# The following approach to retrieve the version number is inspired by this
# comment:
#
#   https://github.com/zestsoftware/zest.releaser/issues/37#issuecomment-14496733
#
# With this approach, development installs always show the right version number
# and do not require a reinstall (as the definition of the version number in
# this setup file would).

version = 'no version defined'
current_dir = os.path.dirname(__file__)
with open(os.path.join(current_dir, "git_cc", "__init__.py")) as f:
    rx = re.compile("__version__ = '(.*)'")
    for line in f:
        m = rx.match(line)
        if m:
            version = m.group(1)

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='git_cc',
    version=version,
    description='Provides a bridge between git and ClearCase',
    long_description=readme,
    author="Charles O'Farrel and others",
    url='https://github.com/charleso/git-cc',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    entry_points={
        'console_scripts': [
            'gitcc=git_cc.gitcc:main',
        ],
    },
)
