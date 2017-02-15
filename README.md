# git-cc

Simple bridge between base ClearCase or UCM and Git.

## Warning

I wrote this purely for fun and to see if I could stop use ClearCase at work
once and for all.

I will probably continue to hack away at it to suite my needs, but I would
love to see it get some real-world polish. (Actually what I would love to see
more is for ClearCase to die, but don't think that's going to happen any time
soon).

Suggestions on anything I've done are more than welcome.

Also, I have made a change recently to support adding binary files which uses
git-cat. Unfortunately git-cat doesn't handle end line conversions and so I
have made gitcc init set core.autocrlf to false. This is only relevant for
Windows users. Don't try changing this after your first commit either as it
will only make matters worse. My apologies to anyone that is stung by this.

## Installation

The easiest way to install git-cc, is to use the Python package installer pip
and install it directly from its GitHub repo. Execute the following command on
the command prompt to install the latest version:

    C:\> pip install git+git://github.com/charleso/git-cc.git#egg=git_cc

If you installed Python from python.org, pip is included with Python 2 >= 2.7.9
and Python 3 >= 3.4. If you do not have pip, [this section] [pip-installation]
from the Python Packaging User Guide describes how to install it.

In case pip or git cannot reach GitHub, for example when such access is not
allowed in the place where you work, you can download the [zip file] [zip-file]
with the latest version from the GitHub repo. Unzip it and use pip to execute
the following command in the root of the directory tree:

    C:\master> pip install .
    
Finally, if you cannot use pip, you can also use the old-skool approach to
install Python packages:

    C:\master> python setup.py install

## Workflow

Initialise:

    git init
    gitcc init d:/view/xyz
    gitcc rebase
    # Get coffee
    # Do some work
    git add .
    git commit -m "I don't actually drink coffee"
    gitcc rebase
    gitcc checkin

Initialise (fast):

Rebase can be quite slow initially, and if you just want to get a snapshot of
ClearCase, without the history, then this is for you:

    gitcc init d:/view/xyz
    gitcc update "Initial commit"

Other:

These are two useful flags for rebase which is use quite frequently.

    gitcc rebase --stash

Runs stash before the rebase, and pops it back on afterwards.

    gitcc rebase --dry-run

Prints out the list of commits and modified files that are pending in ClearCase.

To synchronise just a portion of your git history (instead of from the
very first commit to HEAD), mark the start point with the command:

    gitcc tag <commit>

To specify an existing ClearCase label while checking in, in order to let your
dynamic view show the version of the element(s) just checked in if your
confspec is configured accordingly, use the command:

    gitcc checkin --cclabel=YOUR_EXISTING_CC_LABEL

Note that the CC label will be moved to the new version of the element, if it is already used.

## Configuration

The file .git/gitcc contains configuration options for gitcc. For example, it
allows you to limit which branches and folders you import from:

    [core]
    include = FolderA|FolderB
    exclude = FolderA/sub/folder|FolderB/other/file
    users_module_path = users.py
    ignore_private_files = False
    debug = False
    type = UCM
    [master]
    clearcase = D:\views\co4222_flex\rd_poc
    branches = main|ji_dev|ji_*_dev|iteration_*_dev
    [sup]
    clearcase = D:\views\co4222_sup\rd_poc
    branches = main|sup

In this case there are two separate git branches, master and sup, which
correspond to different folders/branches in ClearCase.

You can add a mapping for each user in your ClearCase history. This is done via
a separate Python module that you provide. An example users module looks
like this:

    users = {
        'charleso': "Charles O'Farrell",\
        'jki': 'Jan Kiszka <jan.kiszka@web.de>',\
    }
     
    mailSuffix = 'example.com'

You specify the path to the users module as the value of key
'users\_module\_path' in the gitcc config file. In the example above, the value
specified is 'users.py'. If the path is relative, it is taken relative to the
location of the config file. So in this example, gitcc will import users.py
from directory .git. But you can also use an absolute users module path.

If you do not specify the users module path in the config file, the ClearCase
user information will be used.

If you make a snapshot of a ClearCase VOB, you copy all the files that are
visible in the view, including view-private files. This might not be what you
want, for example if the VOB contains all kinds of build artifacts. To only
copy the files that are actually under ClearCase control, set the key
'ignore\_private\_files' to True.

## Notes

Can either work with static or dynamic views. I use dynamic at work because
it's much faster not having to update. I've done an update in rebase anyway,
just-in-case someone wants to use it that way.

Can also work with UCM, which requires the 'type' config to be set to 'UCM'.
This is still a work in progress as I only recently switched to this at work.
Note the the history is still retrieved via lshistory and not specifically from
any activity information. This is largely for convenience for me so I don't have
to rewrite everything. Therefore things like 'recommended' baselines are ignored.
I don't know if this will cause any major dramas or not.

## Troubleshooting

1. WindowsError: [Error 2] The system cannot find the file specified

You're most likely running gitcc under Windows Cmd. At moment this isn't
supported. Instead use Git Bash, which is a better console anyway. :-)

If you have both msysgit and Cygwin installed then it may also be
[this](https://github.com/charleso/git-cc/issues/10) problem.

2. cleartool: Error: Not an object in a vob: ".".

The ClearCase directory you've specified in init isn't correct. Please note
that the directory must be inside a VOB, which might be one of the folders
inside the view you've specified.

3. fatal: ambiguous argument 'ClearCase': unknown revision or path not in the working tree.

If this is your first rebase then please ignore this. This is expected.

4. pathspec 'master_cc' did not match any file(s) known to git

See Issue [8](https://github.com/charleso/git-cc/issues/8).

## Behind the scenes

A smart person would have looked at other git bridge implementations for
inspiration, such as git-svn and the like. I, on the other hand, decided to go
cowboy and re-invent the wheel. I have no idea how those other scripts do their
business and so I hope this isn't a completely stupid way of going about it.

I wanted to have it so that any point in history you could rebase on-top of the
current working directory. I've done this by using the ClearCase commit time
for git as well. In addition the last rebased commit is tagged and is used
to limit the history query for any chances since. This tagged changeset is
therefore also used to select which commits need to be checked into ClearCase.

## Problems

It is worth nothing that when initially importing the history from ClearCase
that files not currently in your view (ie deleted) cannot be reached without
a config spec change. This is quite sad and means that the imported history is
not a true one and so rolling back to older revisions will be somewhat limited
as it is likely everything won't compile. Other ClearCase importers seem
restricted by the same problem, but none-the-less it is most frustrating. Grr!

## For developers

This section provides information for git-cc developers.

### Required packages

To develop git-cc, several Python packages are required that are not part of
the standard Python distribution and that you have to install separately. As
these packages might conflict with your system Python environment, you are
strongly advised to set up a [virtualenv] [virtualenv] for your work.

The file 'requirements.txt', which is in the root of the repo, lists the Python
packages that are needed for development. To install these packages, use the
following command:

    git-cc $ pip install -r requirements.txt

### Testing

git-cc comes with a small suite of unit tests, which you can find in
subdirectory tests/. There are several ways to run the unit tests. For example,
you can let Python search for the unit tests and run them in the current Python
environment. To do so, execute the following command *from the root of the
repo*:

    git-cc $ python -m unittest discover tests/

This will result in output such as this:

    ........
    ----------------------------------------------------------------------
    Ran 8 tests in 0.002s
     
    OK

If you run the unit tests from the root of the repo, all unit tests will be
able to import the git-cc package even when it is not installed. If you run the
unit tests from another directory, you have to install git_cc first.

Another way to run the unit test is to use the Python tool [tox] [tox]. tox
does more than just run the unit tests:

- it creates a source distribution of your Python package for each Python
  interpreter that you specify,
- it creates a virtualenv for each Python interpreter you specify, and
- for each virtualenv, installs the package using the source distribution and
  runs the unit tests.

If you execute tox from the root of the repo, its output will look like this:

    git-cc $ tox
    GLOB sdist-make: /home/a-user/repos/github.com/git-cc/setup.py
    py27 inst-nodeps: /home/a-user/repos/github.com/git-cc/.tox/dist/git_cc-1.0.0.dev0.zip
    py27 installed: git-cc==1.0.0.dev0
    py27 runtests: PYTHONHASHSEED='2322284388'
    py27 runtests: commands[0] | python -m unittest discover tests/
    ........
    ----------------------------------------------------------------------
    Ran 8 tests in 0.003s
     
    OK
    py34 inst-nodeps: /home/a-user/repos/github.com/git-cc/.tox/dist/git_cc-1.0.0.dev0.zip
    py34 installed: git-cc==1.0.0.dev0
    py34 runtests: PYTHONHASHSEED='2322284388'
    py34 runtests: commands[0] | python -m unittest discover tests/
    ........
    ----------------------------------------------------------------------
    Ran 8 tests in 0.002s
     
    OK

As the output shows, tox runs the tests in virtualenvs for Python 2.7 and
Python 3.4. This has been specified in file tox.ini, which you can find in the
root of the repo:

    [tox]
    envlist = py27,py34
    [testenv]
    commands=python -m unittest discover tests/

This only works if you have both interpreters installed. If you want to support
other Python versions, you have to update the ini file accordingly.

tox makes it easy to test your Python package in multiple Python
environments. Running tox takes more time than just running the unit tests in
your current environment. As such, developers run it less often, for example
only before a new release or pull request.

### Changes and versioning

The repo contains a CHANGES file that lists the changes for each git-cc release
and for the version currently under development. This file has a specific
format that best can be explained by an example. Assume the CHANGES file looks
like this - note that the actual CHANGES file for git-cc looks different:

    Changelog
    =========

    1.2.0 (unreleased)
    ------------------
    
    - Fixes issue Z

    1.1.0 (2016-02-03)
    ------------------
    
    - Adds support for feature Y
    - Updates documentation of feature X

    1.0.0 (2016-01-03)
    ------------------
     
    - Started versioning at 1.0.0

The file mentions that versions 1.0.0 and 1.1.0 have been released and that the
next version will be 1.2.0.

The process of putting a new release out can be cumbersome and error prone: you
have to update the CHANGES file and setup.py, create a tag, update the CHANGES
file and setup.py again for the development version, etc. For git-cc, the
process of creating a release is fully automated using tools provided by Python
package [zest.releaser] [zest-releaser].

To show how zest.releaser works, the following is the (sanitized) output of the
zest.releaser command 'fullrelease' with the example CHANGES file:

    # execute fullrelease on the command-line
    git-cc $ fullrelease
    
    # the command outputs the beginning of the CHANGES file 
    Changelog entries for version 1.2.0:
     
    1.2.0 (unreleased)
    ------------------
     
    - Fixes issue Z
     
    1.1.0 (2016-02-03)
    ------------------
    # the command proposes to set the release version to 1.2.0
    Enter version [1.2.0]:    
    # pressed RETURN to accept the proposed release version
    # the command automatically updates the CHANGES file and the version number used by setup.py
    
    OK to commit this (Y/n)?
    # pressed RETURN to commit the changes
    
    Tag needed to proceed, you can use the following command:
    git tag 1.2.0 -m "Tagging 1.2.0"
    Run this command (Y/n)?
    # pressed RETURN to tag the release
    
    Check out the tag (for tweaks or pypi/distutils server upload) (Y/n)? n
    # answered 'n' and pressed RETURN to not check out the tag
    
    Current version is 1.2.0
    # the command proposes to set the development version to 1.2.1dev0
    Enter new development version ('.dev0' will be appended) [1.2.1]: 
    # pressed RETURN to accept the proposed development version
    # the command automatically updates the CHANGES file and the version number used by setup.py
    
    OK to commit this (Y/n)? 
    # pressed RETURN to commit the changes

    OK to push commits to the server? (Y/n)? n
    # answered 'n' and pressed RETURN to not push the latest commit yet

When the command is done, the beginning of the CHANGES file has changed to this:

    Changelog
    =========
     
    1.2.1 (unreleased)
    ------------------
     
    - Nothing changed yet.
     
     
    1.2.0 (2016-07-01)
    ------------------
     
    - Fixes issue Z

[pip-installation]: https://packaging.python.org/en/latest/installing/#requirements-for-installing-packages
[tox]: http://tox.readthedocs.io/en/latest/
[virtualenv]: https://virtualenv.pypa.io/en/stable/
[zest-releaser]: http://zestreleaser.readthedocs.io/en/latest/index.html
[zip-file]: https://github.com/charleso/git-cc/archive/master.zip
