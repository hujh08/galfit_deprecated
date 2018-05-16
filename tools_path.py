#!/usr/bin/env python3

import os

def abs_dirname(fname):
    return os.path.abspath(os.path.dirname(fname))

def abs_join(path, fname):
    return os.path.abspath(os.path.join(path, fname))

def rel_chdir(fname, src, dest):
    absdir=abs_join(src, fname)
    return os.path.relpath(absdir, start=dest)