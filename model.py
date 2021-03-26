#!/usr/bin/env python3

'''
    class of models

    Transforming between some models is also allowed
        like from 'expdisk' to 'sersic'

    Note:
        some transforamtions allowed here are not reversible
            like from 'sersic' to 'expdisk'
        these are just empirical treating
'''

import warnings

from collection import GFSlotsDict, is_str_type
from parameter import Parameter

class Model(GFSlotsDict):
    '''
        basi class to handle model of galfit
    '''

    # some setups, see metaclass `MetaSlotsDict` for detail
    keys_sorted=[*'0123456789', '10', 'Z']
    keys_optional=set('0Z')

    keys_alias={
        '0': ['name', 'modname'],
        '1': ['x0'],
        '2': ['y0'],
        '3': ['mag'],
        '4': ['re'],
        '5': ['n'],
        '9': ['ba'],
        '10': ['pa'],
        'Z': ['skip']
    }

    keys_comment={
        '0' : 'Component type',
        '1' : 'Position x, y',
        '3' : 'Integrated magnitude',
        '4' : 'R_e (effective radius) [pix]',
        '5' : 'Sersic index n (de Vaucouleurs n=4)',
        '9' : 'Axis ratio (b/a)',
        '10': 'Position angle [deg: Up=0, Left=90]',
        'Z' : 'Skip this model? (yes=1, no=0)'
    }

    ## values example for all models
    values_example={i: Parameter(0) for i in keys_sorted[1:-1]}
    values_example['0']=''
    values_example['Z']=0

    ## str format
    _fmt_float='%.4f'
    _line_fmt2='%2s) %s'            # formt for 2 fields
    _line_fmt3='%2s) %-22s #  %s'   # formt for 3 fields

    # reload init_class
    @classmethod
    def init_class(cls):
        '''
            reload init_class to do additional action to class

            like copy some existed setup in Model
        '''
        # some check 
        assert cls.keys_sorted[0]=='0' and cls.keys_sorted[-1]=='Z'

        # copy attrs
        if cls.__name__!='Model':  # no do to :class Model
            cls.copy_to_subclass()

        super().init_class()

    @classmethod
    def copy_to_subclass(cls):
        '''
            copy default setup from parent to subclass
        '''
        # values default of mode name
        cls.values_default={'0': cls.get_model_name()}

        # copy default setup from parent
        props_copy=['keys_alias', 'values_example', 'keys_comment',
                    'values_default']
        parent=cls.__bases__[0]   # only copy from first bases

        for prop in props_copy:
            if prop not in cls.__dict__:
                continue

            val=getattr(cls, prop)
            val0=getattr(parent, prop)

            for k in cls.keys_sorted:
                if k not in val and k in val0:
                    val[k]=val0[k]

    # about model
    ## special model
    @classmethod
    def is_sky(cls):
        '''
            wheter the model is for sky

            there would be some special treatment for sky model
        '''
        return cls.get_model_name()=='sky'

    @classmethod
    def need_psize(cls):
        '''
            wheter the model need pixel size (Parameter P in header of galfit file)
                    to calculate suface brightness in Parameter (3)
                        instead of integrated magnitude
        '''
        mods=set(['nuker', 'ferrer', 'king'])
        name=cls.get_model_name()
        return name in mods

    ## model name
    @classmethod
    def get_model_name(cls):
        '''
            model name
        '''
        return cls.__name__.lower()

    ## implemented models
    @staticmethod
    def get_all_models():
        '''
            return a map between model name and its class
        '''
        return {m.__name__.lower(): m for m in Model.__subclasses__()}

    @staticmethod
    def get_model_class(name):
        '''
            return a class for a given model name
        '''
        return Model.get_all_models()[name.lower()]

    # reload prop setter

    # stringlizing
    def line_for_print_model_name(self):
        '''
            line for model name
        '''
        key='0'
        name=self.name
        comments='Component type'

        return self._line_fmt3 % (key, name, comments)

    def strprint_of_val_key(self, key):
        '''
            reload function for val str for key
        '''
        if not self.is_sky():
            if key=='2':  # merge '2' to '1'
                return None
            if key=='1':
                x0=self.get_val('1')
                y0=self.get_val('2')

                sx=x0.str_val()
                sy=y0.str_val()

                s='%s %s  %i %i' % (sx, sy, x0.state, y0.state)

                return s

        return super().strprint_of_val_key(key)

    # fitting parameters
    def get_all_fitpars(self):
        '''
            return a list of key, each for a fitting parameter
        '''
        keys=[]
        for k in self.keys_sorted:
            if self.is_fitpar_key(k):
                keys.append(k)
        return keys

    def is_fitpar_key(self, key):
        '''
            determine whether a key is a fitting parameter
        '''
        key=self.get_std_key(key)
        return self.is_valid_key(key) and key not in '0Z'

    def is_xypar_key(self, key):
        '''
            if key is '1' (not alias x0), it might mean setting to both xy
        '''
        return (not self.is_sky()) and key=='1'

    ## set methods
    def set_fitpar(self, key, val):
        '''
            set a fitting parameter

            there is special key, '1' to set both xy
        '''
        assert self.is_fitpar_key(key)

        # for xy parameters
        if self.is_xypar_key(key) and is_str_type(val):
            val=val.split()
            if len(val)==4:
                self.set_fitpar('1', val[::2])
                self.set_fitpar('2', val[1::2])
                return

        if not self.is_set_key(key):
            if not self.is_opt_key(key):
                return super().set_prop(key, val)
            self.touch_opt_key(key)

        self.get_val(key).update(val)

    def update_fitpar(self, key, **kwargs):
        '''
            update state (value, state, uncertainty)
                of a fitting parameter
        '''
        assert self.is_fitpar_key(key)

        if not self.is_set_key(key):
            if not self.is_opt_key(key):
                raise Exception('cannot update missing required parameter: '
                                +self.get_key_name(key))
            self.touch_opt_key(key)
        self.get_val(key).update(**kwargs)

    ### reload `set_prop` to handle fitting parameters
    def set_prop(self, key, val):
        '''
            reload `set_prop` for fitting parameters
        '''
        if self.is_fitpar_key(key):
            return self.set_fitpar(key, val)
        super().set_prop(key, val)

    ## free/freeze fitting parameters
    def set_fit_state(self, state, pars=None):
        '''
            set fit state (free/freeze to fit) for fitting parameters

            if `pars` is None, do to all fitting parameters

            `state` could be int or str
                for str, it could be str of int, or 'free'/'freeze'
        '''
        if pars is None:
            pars=self.get_all_fitpars()

        for k in pars:
            self.update_fitpar(k, state=state)

    def free(self, pars=None):
        '''
            free part/all fitting parameters
        '''
        self.set_fit_state('free', pars)

    def freeze(self, pars=None):
        '''
            free part/all fitting parameters
        '''
        self.set_fit_state('freeze', pars)

## frequently used models
class Sersic(Model):
    '''
        Sersic Profile
    '''
    # setup for model
    keys_sorted=[*'0123459', '10', 'Z']

    # transform to other models
    def to_devauc(self):
        '''
            to De Vaucouleurs model
        '''
        n=self.n.val

        if n!=4:
            warnings.warn('irreversible transform from Sersic to Devauc')

        m=Devauc()

class Sky(Model):
    '''
        Background Sky
    '''
    # setup for model
    keys_sorted='0123Z'
    keys_optional=set('0123Z')

    keys_alias={
        '1': ['bkg'],
        '2': ['dbdx'],
        '3': ['dbdy'],
    }

    keys_comment={
        '1' : 'Sky background [ADUs]',
        '2' : 'dsky/dx [ADUs/pix]',
        '3' : 'dsky/dx [ADUs/pix]',
    }

    ## str format
    _fmt_float='%.3e'

class Expdisk(Model):
    '''
        Exponential Disk Profile
    '''
    # setup for model
    keys_sorted=[*'012349', '10', 'Z']

    keys_alias={
        '4': ['rs'],
    }

    keys_comment={
        '4' : 'R_s (disk scale-length) [pix]',
    }

    # model 

class Edgedisk(Model):
    '''
        Edge-On Disk Profile
    '''
    # setup for model
    keys_sorted=[*'012345', '10', 'Z']
    keys_alias={
        '3': ['sb'],
        '4': ['dh'],
        '5': ['dl'],
    }

    keys_comment={
        '3' : 'central surface brightness [mag/arcsec^2]',
        '4' : 'disk scale-height [Pixels]',
        '5' : 'disk scale-length [Pixels]',
    }

class Devauc(Model):
    '''
        de Vaucouleurs Profile
    '''
    # setup for model
    keys_sorted=[*'012349', '10', 'Z']

class PSF(Model):
    '''
        PSF Profile
    '''
    # setup for model
    keys_sorted=[*'0123', 'Z']

## other models, not used so frequently for me
class Nuker(Model):
    '''
        Nuker Profile
    '''
    # setup for model
    keys_sorted=[*'012345679', '10', 'Z']

    keys_alias={
        '3': ['ub'],  # mu at Rb
        '4': ['rb'],
        '5': ['alpha'],
        '6': ['beta'],
        '7': ['gamma'],
    }

    keys_comment={
        '3' : 'mu(Rb) [surface brightness mag. at Rb]',
        '4' : 'Rb [pixels]',
        '5' : 'alpha (sharpness of transition)',
        '6' : 'beta (outer powerlaw slope)',
        '7' : 'gamma (inner powerlaw slope)',
    }

class Moffat(Model):
    '''
        Moffat Profile
    '''
    # setup for model
    keys_sorted=[*'0123459', '10', 'Z']

    keys_alias={
        '4': ['fwhm'],
        '5': ['pl'],
    }

    keys_comment={
        '4' : 'FWHM [Pixels]',
        '5' : 'powerlaw',
    }

class Ferrer(Model):
    '''
        Modified Ferrer Profile
    '''
    # setup for model
    keys_sorted=[*'01234569', '10', 'Z']

    keys_alias={
        '3': ['mu', 'sb'],  # sb for surface brightness
        '4': ['tr'],
        '5': ['alpha'],
        '6': ['beta'],
    }

    keys_comment={
        '3' : 'Central surface brightness [mag/arcsec^2]',
        '4' : 'Outer truncation radius [pix]',
        '5' : 'Alpha (outer truncation sharpness)',
        '6' : 'Beta (central slope)',
    }

class Gaussian(Model):
    '''
        Gaussian Profile
    '''
    # setup for model
    keys_sorted=[*'012349', '10', 'Z']

    keys_alias={
        '4': ['fwhm'],
    }

    keys_comment={
        '4' : 'FWHM [Pixels]',
    }

class King(Model):
    '''
        Empirical (Modified) King Profile
    '''
    # setup for model
    keys_sorted=[*'01234569', '10', 'Z']

    keys_alias={
        '3': ['mu', 'sb'],
        '4': ['rc'],
        '5': ['rt'],
        '6': ['alpha'],
    }

    keys_comment={
        '3' : 'Central surface brightness [mag/arcsec^2]',
        '4' : 'Rc',
        '5' : 'Rt',
        '6' : 'alpha',
    }
