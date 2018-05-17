#!/usr/bin/env python3

import os

# use realpath, not abspath, to eliminate symbolic links
abspath=os.path.realpath

def abs_dirname(fname):
    return abspath(os.path.dirname(fname))

def abs_join(path, fname):
    return abspath(os.path.join(path, fname))

def rel_chdir(fname, src, dest):
    absdir=abs_join(src, fname)
    return os.path.relpath(absdir, start=dest)