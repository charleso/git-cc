from __future__ import print_function

import os
import sys

if __name__ == '__main__':

    for f in os.listdir(sys.argv[1]):
        print(f)
