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

    ## add/remove/duplicate model
    def add_comp(self, mod, vals=None, index=None, keys=None, Z=None):
        '''
            add a component in `comps` before index `index`
                if `index` is None, insert in the end

            Parameter:
                mod: instance of galfit Model, model class, or str
                    if the latter two,
                        use :param vals, keys, Z to create an instance
        '''
        if not Model.is_gf_model_instance(mod):
            if is_str_type(mod):
                mod=Model.get_model_class(mod)
            elif not Model.is_gf_model_class(mod):
                raise Exception('only accept galfit model instance/class or str as mod, '
                                'but got '+type(mod).__name__)
            mod=mod()
            if vals is not None:
                mod.set_fitpars_val(vals, keys=keys)

            if Z is not None:
                mod.Z=Z

        # insert
        if index is None:
            index=len(self.comps)
        self.comps.insert(index, mod)

    def del_comp(self, index):
        '''
            delete comp
        '''
        del self.comps[index]

    def dup_comp(self, index, index_dup=None):
        '''
            duplicate component 
                and then insert just after it by default
                    or other index, given by `index_dup`
        '''
        comp=self.comps[index].copy()

        if index_dup is None:
            if index==-1:
                index_dup=len(self.comps)
            else:
                index_dup=index+1

        self.comps.insert(index_dup, comp)

    ### add particular model
    def add_sersic(self, *args, **kwargs):
        '''
            add sersic model
        '''
        self.add_comp('sersic', *args, **kwargs)

    def add_sky(self, *args, **kwargs):
        '''
            add sky model
        '''
        self.add_comp('sky', *args, **kwargs)

    ## model transform inplace
    def trans_comp_to(self, index, mod, warn=True):
        '''
            transform component to a given model

            Parameter:
                index: int
                    index of component to transform

                mod: str, galfit model class or instance
                    see `Model:mod_trans_to` for detail
        '''
        comp=self.comps[index]

        self.comps[index]=comp.mod_trans_to(mod, warn=warn)

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
