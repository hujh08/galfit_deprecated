#!/usr/bin/env python3

'''
    Header of galfit file
'''

from collection import GFSlotsDict

class Header(GFSlotsDict):
    '''
        class to handle header of galfit file
    '''
    # default set up
    ## keys
    keys_sorted='ABCDEFGHIJKOP'  # file writed in this order
    # keys_valid=set(keys_sorted)

    ## user-friendly name of keys
    keys_name=dict(
        A='input image',
        B='output image block',
        C='sigma file',
        D='psf file',
        E='psf sampling factor',
        F='mask file',
        G='constraint file',
        H='fit region',
        I='convolution box',
        J='magnitude zeropoint',
        K='pixel size',   # plate scale (dx, dy), [arcsec per pixel]
        O='display type',
        P='fit mode',
    )

    ## comments of parameters
    keys_comment=dict(
        A='Input data image (FITS file)',
        B='Output data image block',
        C='Sigma image',
        D='Input PSF image',
        E='PSF fine sampling factor relative to data',
        F='Bad pixel mask',
        G='File with parameter constraints (ASCII file)',
        H='Image region',
        I='Size for convolution (x y)',
        J='Magnitude photometric zeropoint',
        K='Plate scale (dx dy)   [arcsec per pixel]',
        O='Display type (regular, curses, both)',
        P='0=optimize, 1=model, 2=imgblock, 3=subcomps',
    )

    ## alias of keys
    keys_alias=dict(  # {key: [alias_names]}
        A=['input'],
        B=['output'],
        C=['sigma'],
        D=['psf'],
        E=['psfFactor'],
        F=['mask'],
        G=['constraints', 'cons'],
        H=['region', 'fitregion', 'xyminmax'],
        I=['conv'],
        J=['zerop'],
        K=['pscale', 'psize'],
        O=['disp'],
        P=['mod'],
    )
    # constructed in metaclass now
    # map_keys_alias=funcs.inverse_alias(keys_alias)

    ## default values
    # values_example
    values_example=dict(
        A='none',
        B='none',        # must give explicitly
        C='none',
        D='none',
        E=1,             # can only be an integer, see readme of galfit
        F='none',
        G='none',
        H=[0, 0, 0, 0],  # must give explicitly
        I=[0, 0],        # must give explicitly
        J=20.,
        K=[1.0, 1.0],    # required for some profiles, but only a shift of mag, like J
        O='regular',
        P='0',
    )
    keys_required=set('BHI')
    # keys_optional=set(keys_sorted).difference()

    ## parameter 'P': mode parameter
    ## 0=optimize, 1=model, 2=imgblock, 3=subcomps
    mode_valid=set('0123')

    ### alias of mode
    mode_alias={
        '0': ['o', 'opt',   'optimize'],
        '1': ['m', 'mod',   'model'],
        '2': ['b', 'block', 'imgblock'],
        '3': ['s', 'sub',   'subcomps'],
    }
    # map_mode_alias=inverse_alias(mode_alias)

    ## parameter 'O': display parameter
    disp_valid={'regular', 'curses', 'both'}

    ## collect of valid values
    values_valid=dict(
        O=disp_valid,
        P=mode_valid,
    )

    ## collect of value alias
    values_alias=dict(
        P=mode_alias,
    )
