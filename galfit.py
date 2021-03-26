#!/usr/bin/env python3

'''
    top layer to handle the whole formatted input file of galfit

    Such a file contains two parts: header and componets
        which would be handled by different modules

    When loading as a instance, the file is parsing line by line
        which is labeled by serveral starting chars followed with `)`
'''

import re

from header import Header
from model import Model
from collection import is_int_type, is_str_type

class GalFit:
    '''
        class to represent whole galfit file
    '''
    def __init__(self, fname=None):
        '''
            initiation could be done from a galfit file,
                or just left as a empty one, waiting to set up
        '''
        # two parts: header and components (models)
        self.header=Header()
        self.comps=[]     # collection of components

        # self.gfdir=None   # dirctory of the file

        # load file
        if fname is None:
            return

        self.load_file(fname)

    # load galfit file
    def load_file(self, fname):
        '''
            load a galfit file
        '''
        # re pattern for labeled line: N) xxx ... # comments
        ptn_lab=re.compile(r'^\s*([0-9a-zA-Z.]+)\)\s+([^#]+?)(?:\s+#|\s*$)')

        with open(fname) as f:
            for line in f:
                m=ptn_lab.match(line)

                if not m:
                    continue
                
                key, val=m.groups()

                if key in self.header:
                    self.header.set_prop(key, val)
                    continue

                if key=='0':
                    mod=Model.get_model_class(val)()
                    self.comps.append(mod)
                    continue

                if key in self.comps[-1]:
                    self.comps[-1].set_prop(key, val)

    # stringlizing
    def __str__(self):
        '''
            user-friendly string
        '''
        lines=['='*80,
               '# IMAGE and GALFIT CONTROL PARAMETERS']
        lines.append(str(self.header))
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

        for i, comp in enumerate(self.comps):
            lines.append('# Component number: %i' % (i+1))
            lines.append(str(comp))
            lines.append('')

        lines.append('='*80)

        return '\n'.join(lines)

    # fetch attribution
    def __getitem__(self, prop):
        '''
            index fetch

            only allow integer and str as index
                str for Header prop
                int to indexing componets
        '''
        if is_str_type(prop):
            return self.header.get_val(prop)
        elif is_int_type(prop):
            return self.comps[prop]
        else:
            raise Exception('index must be str or integer, '
                            'not '+type(prop).__name__)

    ## write to file
    def writeto(self, fname):
        with open(fname, 'w') as f:
            f.write(str(self))

    # functions to model
    ## fitting parameter
    def set_fit_state(self, state, comps=None):
        '''
            free/freeze fitting parameters to all/part components

            :param comps: None, or list of int
        '''
        if comps is None:
            comps=self.comps
        else:
            comps=[self.comps[i] for i in comps]

        for comp in comps:
            comp.set_fit_state(state)

    def free(self, comps=None):
        '''
            free all fitting parameters to all/part components
        '''
        self.set_fit_state('free', comps)

    def freeze(self, comps=None):
        '''
            freeze all fitting parameters to all/part components
        '''
        self.set_fit_state('freeze', comps)

    # Functions to image
    def imcopy_to(self, fitsname):
        '''
            work like IRAF task imcopy, but to input image
        '''
        pass

    def imedit_to(self, fitsname):
        '''
            work like IRAF task imedit, but to input image
        '''
        pass


    # Functions of model
    def insert_model(self, mod, i):
        '''
            insert a model before current `i`th model
        '''
        pass

    def duplicate_model(self, i):
        '''
            duplicate the `i`th model in-place
        '''
        pass

    '''
        constraint:
        treat constraint file as independent, just as other, like mask, sigma files
        not trace it in class, just writting to file immediately whenover change happens
    '''