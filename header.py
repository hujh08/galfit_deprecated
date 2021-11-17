#!/usr/bin/env python3

'''
    Header of galfit file
'''

import os

from .collection import GFSlotsDict, is_int_type
from .constraint import Constraints

class Header(GFSlotsDict):
    '''
        class to handle header of galfit file

        some parameters in header relate to a file in system
            like input image, mask file, sigma fits, et al.
        To handle them, a path information is also stored in the information
            which is initiated by the path of galfit file
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
        '0': ['optimize', 'opt', 'o'],
        '1': ['model', 'mod', 'm'],
        '2': ['imgblock', 'block', 'b'],
        '3': ['subcomps', 'sub', 's'],
    }

    #### user-friendly mode
    mode_names={k: a[0] for k, a in mode_alias.items()}

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

    # init
    def __init__(self, *args, **kwargs):
        '''
            add property 'dir_hdr': directory of the file in header
                it is used to handle the parameters related to file in system
                    like input image, mask file, sigma fits, et al.
        '''
        super().__init__(*args, **kwargs)
        self.__dict__['dir_hdr']=''  # use cwd by default

    ## reset
    def reset(self):
        '''
            reset header
        '''
        super().reset()
        self.dir_hdr=''

    ## set attr to handle `dir_hdr`
    def __setattr__(self, prop, val):
        '''
            handle additional property `dir_hdr`
        '''
        if prop=='dir_hdr':
            return self.set_dir_hdr(val)
        return super().__setattr__(prop, val)

    # reload getattr to handle mode parameter
    def __getattr__(self, prop):
        '''
            reload to return user-friendly mode
        '''
        v=super().__getattr__(prop)
        if self.get_std_key(prop)=='P':
            if v in self.mode_names:
                v=self.mode_names[v]
        return v

    ## frequently used functions for mod set
    def set_gf_mod(self, mod):
        '''
            set Parameter P (galfit runing mode)

            support mod to be string or int
                0=optimize, 1=model, 2=imgblock, 3=subcomps
        '''
        if is_int_type(mod):
            assert 0<=mod<=3
            mod='%i' % mod
        self.set_prop('P', mod)

    def set_fit_mod(self):
        '''
            set optimize mode for galfit input file
        '''
        self.set_gf_mod(0)

    def set_create_mod(self, block=False, subcomps=False):
        '''
            no optimizing, just create images
                1=model, 2=imgblock, 3=subcomps

            2 bool arguments: block, subcomps
                if `subcomps` is true, mode=3 (ignoring `block`)
                otherwise, if `block` is true, mode=2
                           otherwise, mode=1
        '''
        if subcomps:
            mod=3
        elif block:
            mod=2
        else:
            mod=1
        self.set_gf_mod(mod)

    # functions to handle parameters related with file
    def load_constraints(self):
        '''
            load constraint file to `Constraints` object

            if 'none', return empty object
        '''
        fname=self.get_file_path('constraints')
        if fname=='none':
            return Constraints()

        return Constraints(fname)

    def set_constraints(self, fname):
        '''
            set constraints
        '''
        fname=os.path.relpath(fname, self.dir_hdr)
        self.set_prop('constraints', fname)

    ## only to `dir_hdr`
    def set_dir_hdr(self, d, force_abs=False):
        '''
            set the `dir_hdr`
                which is used to handle file parameters
                    like input image, mask file, et al.

            bottom function to set `dir_hdr`

            `force_abs`: bool
                if true, force dir_hdr to be absolute path
        '''
        self.__dict__['dir_hdr']=d

        if force_abs:
            self.to_abs_dir_hdr()

    def to_abs_dir_hdr(self):
        '''
            use absolute path for `dir_hdr`
        '''
        self.set_dir_hdr(os.path.abspath(self.dir_hdr))

    ## file parameters, which are related to a file in system
    keys_filepar='ACDFG'  # input, sigma, psf, mask, constraints. No output!

    ## set file parameters
    def chdir_to(self, dst, keys_fix=None):
        '''
            change the header directory to a new one, `dst`
                which might be directory where to run galfit

            file parameters would change to relative path starting from `dst`
            `dir_hdr` would also reset to `dst`

            :param keys_fix: optional, keys to keep fixed
                if None, change all parameters

                used when to keep some parameters unchanging
        '''
        # keys
        keys=self.keys_filepar
        if keys_fix is not None:
            keys_fix=set([self.get_std_key(k) for k in keys_fix])
            keys=[k for k in keys if k not in keys_fix]

        # abspath of dst, src
        dst=os.path.abspath(dst)
        src=os.path.abspath(self.dir_hdr)

        if src==dst:  # directory unchanged
            return

        # change file pars to relpath
        for k in keys:
            fname=self.get_val(k)
            if fname=='none':
                continue

            fname=os.path.join(src, fname)
            self.set_prop(k, os.path.relpath(fname, dst))

        # reset `dir_hdr`
        self.set_dir_hdr(dst)

    #### frequently used
    def chdir_to_subd(self, subd, **kwargs):
        '''
            change to a subdirectory of `dir_hdr`
        '''
        dst=os.path.join(self.dir_hdr, subd)
        self.chdir_to(dst, **kwargs)

    def chdir_to_parent(self, up=1, **kwargs):
        '''
            change to parent of `dir_hdr`

            up: int
                how many levels upper of `dir_hdr` to go
        '''
        assert up>=1
        dst=os.path.join(self.dir_hdr, *(['..']*up))
        self.chdir_to(dst, **kwargs)

    ## get file parameters
    def get_file_path(self, key, return_abs=False):
        '''
            get path for a file parameter
        '''
        assert self.get_std_key(key) in self.keys_filepar

        fname=self.get_val(key)
        if fname=='none':
            return fname

        path=os.path.join(self.dir_hdr, fname)
        if return_abs:
            path=os.path.abspath(path)

        return path