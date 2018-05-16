#!/usr/bin/env python3

# path used in galfit inside

import re

def keys_set(keys, pref='', suff=''):
    return {pref+k+suff for k in keys}

def keys_patt(keys, prefs=[], suffs=[]):
    restr='(?P<key>%s)' % '|'.join(keys)

    if prefs:
        prefs_str='|'.join(prefs)
        restr='(%s)' % prefs_str+restr

    if suffs:
        suffs_str='|'.join(suffs)
        restr=restr+'(%s)' % prefs_str

    return re.compile(restr+'$')

# skycoord
def radec2skycoord(*args):
    if len(args)>2:
        raise Exception('expect at most 2 arguments, '+
                        'but got %i' % len(args))
    from astropy.coordinates import SkyCoord
    if len(args)==1:
        args=tuple(args[0])
    return SkyCoord(*args, unit='deg')