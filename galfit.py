#!/usr/bin/env python3

'''
class to hold parameters to run galfit
'''

import os

from .head import Head
from .model import Model
from .fitlog import FitLogs
from .tools import gfname

class GalFit:
    def __init__(self, filename=None, fitlog=False):
        self.__dict__['comps']=[]  # collection of components
        self.__dict__['head']=Head()

        if filename!=None:
            if type(filename)==int:
                filename=gfname(filename)

            dirname=os.path.dirname(filename)
            if dirname and dirname!='.':
                self.filename=os.path.basename(filename)
                self.gfpath=dirname
            else:
                self.filename=filename

            self._load_file(filename)

        if fitlog:
            self._load_fitlog(fitlog)

    # methods of construction
    def _load_file(self, filename):
        blk=self.head   # current block
        with open(filename) as f:
            for line in f:
                if line.startswith('#  Input menu file: '):
                    self.init_file=line.split()[-1]
                    continue

                line=line.strip()
                if not line or line[0]=='#':
                    continue

                key, *vals=line.split()
                if key[-1]!=')':
                    continue

                key=key[:-1]
                if key=='0':
                    mdname=vals[0]
                    blk=Model.get_model(mdname)()
                    self.comps.append(blk)

                if key in blk.valid_keys:
                    blk._feed_key_fields(key, vals)

    def _load_fitlog(self, fitlog):
        if type(fitlog)!=str:
            fitlog='fit.log'
        logs=FitLogs(fitlog)
        if not hasattr(self, 'init_file'):
            log=logs.get_log(self.filename)
        else:
            log=logs.get_log(self.init_file, self.filename)

        for mod, lmod in zip(self.comps, log.mods):
            mod.set_uncerts(lmod.uncerts)
            mod.set_flags(lmod.flags)

    # handle head
    ## input data image
    def get_fits_hdu(self):
        from astropy.io import fits
        fitsname=self.input
        if fitsname[-1]==']':
            fitsname, hduid=fitsname[:-1].split('[')
            hduid=int(hduid)
        else:
            hduid=0

        if hasattr(self, 'gfpath'):
            fitsname=os.path.join(self.gfpath, fitsname)

        return fits.open(fitsname)[hduid]

    # handle components
    ## add/remove component
    def add_comp(self, mod, vals=None, fixeds=None, Z=0, index=0):
        '''
        add component before index
        '''
        if isinstance(mod, Model):
            modnew=mod
        elif type(mod)==str or type(mod)==type:
            if type(mod)==str:
                mod=Model.get_model(mod)
            elif not issubclass(mod, Model):
                raise TypeError('unsupported model type: %s' % type(mod))
            modnew=mod(vals=vals, fixeds=fixeds, Z=Z)
        else:
            raise TypeError('unsupported model type: %s' % type(mod))

        self.comps.insert(index, modnew)

    def del_comp(self, index=0):
        '''
        delete comp
        '''
        del self.comps[index]

    ### some specific models
    def add_sersic(self, *args, **keys):
        from .model import Sersic
        self.add_comp(Sersic, *args, **keys)

    def add_sky(self, *args, **keys):
        from .model import Sky
        self.add_comp(Sky, *args, **keys)

    # magic methods
    def __getattr__(self, prop):
        if prop in self.head.alias_keys:
            return getattr(self.head, prop)
        
        raise AttributeError(prop)

    def __setattr__(self, prop, val):
        if prop in self.head.alias_keys:
            setattr(self.head, prop, val)
        elif prop in {'filename', 'init_file', 'gfpath'}:
            # local property
            super().__setattr__(prop, val)
        else:
            raise AttributeError(prop)

    # output
    def _reset_comps_id(self, start=1):
        for i, comp in enumerate(self.comps, start):
            comp.set_id(i)

    def write(self, filename, overwrite=True):
        if type(filename)==int:
            filename=gfname(filename)
        with open(filename, 'w') as f:
            f.write(self.__str__())
            f.write('\n')

    def __str__(self):
        lines=['='*80,
               '# IMAGE and GALFIT CONTROL PARAMETERS']
        lines.append(str(self.head))
        lines.append('')
        lines.append('# INITIAL FITTING PARAMETERS')
        lines.append('#')
        lines.append('#   For component type, the allowed functions:')
        lines.append('#     sersic, expdisk, edgedisk, devauc,')
        lines.append('#     king, nuker, psf, gaussian, moffat,')
        lines.append('#     ferrer, and sky.')
        lines.append('#')
        lines.append('#   Hidden parameters appear only when specified:')
        lines.append('#     Bn (n=integer, Bending Modes).')
        lines.append('#     C0 (diskyness/boxyness),')
        lines.append('#     Fn (n=integer, Azimuthal Fourier Modes).')
        lines.append('#     R0-R10 (coordinate rotation, for spiral).')
        lines.append('#     To, Ti, T0-T10 (truncation function).')
        lines.append('#')
        lines.append('# '+'-'*78)
        lines.append('#   par)    par value(s)    fit toggle(s)')
        lines.append('# '+'-'*78)
        lines.append('')

        self._reset_comps_id()
        for comp in self.comps:
            lines.append('# Component number: %i' % comp.id)
            lines.append(str(comp))
            lines.append('')

        lines.append('='*80)

        return '\n'.join(lines)
