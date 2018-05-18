#!/usr/bin/env python3

import os

def abspath(path):
    '''expand symbolic links of directories, not files'''
    absp=os.path.abspath(path)
    if os.path.isdir(absp) or not os.path.islink(absp):
        return os.path.realpath(absp)
    dirn=os.path.dirname(absp)
    basn=os.path.basename(absp)
    return os.path.join(os.path.realpath(dirn), basn)

def abs_dirname(fname):
    return abspath(os.path.dirname(fname))

def abs_join(path, fname):
    return abspath(os.path.join(path, fname))

def rel_chdir(fname, src, dest):
    absdir=abs_join(src, fname)
    return os.path.relpath(absdir, start=dest)