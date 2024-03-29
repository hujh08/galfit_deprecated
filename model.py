#!/usr/bin/env python3

'''
class for galfit supported model
'''

from functools import partial

from .collection import Collection
from .parameter import Parameter
from .containers import Container

from .tools_gf import keys_set

class Model(Collection):
    '''
    basic class for model

    Properties
    ----------
    parameters: of class Parameters
    Z: boolean
    '''
    default_values=[0]*10

    fmt_value=4  # precise
    len_valstr=24
    len_keystr=2

    comments={
        '0' : 'Component type',
        '1' : 'Position x, y',
        'Z' : 'Skip this model? (yes=1, no=0)'
    }

    valid_props={'params', 'id', 'name', 'Z'}

    def __init__(self, vals=None, tofits=None, Z=0, id=-1):
        super().__init__(Parameter)
        self.id=int(id)  # id used for output
        self.Z=Container(0)
        self.name=self.__class__.__name__.lower()

        self.Z.set(Z)
        if vals!=None:
            self.set_vals(vals)
        if tofits!=None:
            self.set_tofits(tofits)

    # copy
    def copy(self):
        newobj=super().copy()
        newobj.id=-1
        newobj.Z=self.Z.copy()
        return newobj

    # basic methods
    def _get_param(self, key):
        if key.lower()=='z':
            return self.Z
        return super()._get_param(key)

    def _feed_key_fields(self, key, fields):
        '''
        feed in fields in a line seperated by whitespace
            except the 1st field,
                which is offered as key after removing the last ')'
        '''
        if key=='1' and not self.is_sky():
            self._set_param('2', [fields[1], fields[3]])
            val=[fields[0], fields[2]]
        elif key=='Z':
            val=fields[0]
        else:
            val=fields[:2]
        self._set_param(key, val)

    # methods to get parameters' information
    def get_num_of_params(self):
        '''
        number of parameters
        '''
        return len(self.valid_keys)

    def get_num_of_fixed_params(self):
        '''
        number of fixed parameters
        '''
        return sum([self._get_param(p).is_frozen() for p in self.valid_keys])

    def get_num_of_free_params(self):
        '''
        number of fixed parameters
        '''
        return self.get_num_of_params()-self.get_num_of_fixed_params()

    # methods to set parameters
    def _gen_set_field(self, vals, field):
        if type(vals)!=dict:
            vals=dict(zip(self.sorted_keys, vals))

        for k in vals:
            getattr(self._get_param(k), 'set_'+field)(vals[k])

    ## free/freeze all parameters
    def set_all_params_fit(self, tofit):
        '''
        set all parameters free to fit if `tofit` is True
        '''
        for p in self:
            p.set_par_fit(tofit)

    def free_all(self):
        self.set_all_params_fit(True)

    def freeze_all(self):
        self.set_all_params_fit(False)

    ## free/freeze part of parameters
    def free_pars(self, pars):
        for p in pars:
            getattr(self, 'par_'+p).free()

    def freeze_pars(self, pars):
        for p in pars:
            getattr(self, 'par_'+p).freeze()

    # visulization
    def get_xy_string(self):
        x0s=self._get_param('x0')._str_fields()
        y0s=self._get_param('y0')._str_fields()
        return ' '.join(map(' '.join, zip(x0s, y0s)))

    def _str(self):
        keys=('0',)+self.sorted_keys+('Z',)
        specials={'0': self.name}
        if not self.is_sky():
            keys=keys[:2]+keys[3:]
            specials['1']=self.get_xy_string()
        return super()._str(keys, specials=specials)

    # methods about model
    def get_model_name(self):
        return self.name

    def set_id(self, id):
        self.id=int(id)

    def is_sky(self):
        return False

    # user method
    def get_xy(self):
        if self.is_sky():
            raise AttributeError('no attribute: xy')

        return self.get_pval('x0'), self.get_pval('y0')

    ## handle Z
    def skip_mod(self):
        self._set_param('Z', 1)

    def keep_mod(self):
        self._set_param('Z', 0)

    @classmethod
    def get_all_models(cls):
        return {m.__name__.lower(): m for m in cls.__subclasses__()}

    @staticmethod
    def get_model(name):
        return Model.get_all_models()[name.lower()]

    # magic methods
    def __contains__(self, prop):
        return prop in self.valid_keys or\
               prop in self.alias_keys or\
               prop.lower() == 'z'

    def __iter__(self):
        return iter([self._get_param(k) for k in self.sorted_keys])

    def __getattr__(self, prop):
        Pkeys=Parameter.valid_keys
        # collect fields, like vals, tofits
        if prop in keys_set(Pkeys, suff='s'):
            return [p[prop[:-1]].get() for p in self]

        # methods to set single field, like set_vals, set_frees
        if prop in keys_set(Pkeys, 'set_', 's'):
            return partial(self._gen_set_field, field=prop[4:-1])

        if not self.is_sky() and prop=='xy':
            return self.get_xy()

        # return Parameter type
        if prop in keys_set(self.alias_keys, 'par_'):
            return self._get_param(prop[4:])

        # return value of parameter
        if prop in self.alias_keys or prop.lower()=='z':
            return super().__getattr__(prop)

    def __str__(self):
        return self._str()

class Sersic(Model):
    '''
    sersic model
    '''
    # setup for model
    ## valid parameters
    sorted_keys=('1', '2', '3', '4', '5', '9', '10')
    valid_keys=set(sorted_keys)

    ## default parameters
    default_values=[0, 0, 20, 10, 2, 1, 0]

    ## alias of parameters
    alias_keys={
        'x0' : '1',
        'y0' : '2',
        'mag': '3',
        're' : '4',
        'n'  : '5',
        'ba' : '9',
        'pa' : '10',
    }

    ## comments for parameters
    comments={
        '3' : 'Integrated magnitude',
        '4' : 'R_e (effective radius) [pix]',
        '5' : 'Sersic index n (de Vaucouleurs n=4)',
        '9' : 'Axis ratio (b/a)',
        '10': 'Position angle [deg: Up=0, Left=90]',
    }

    # handle parameters
    def scale_re(self, scale):
        # scale effective radius
        self.re*=scale

    def change_shape_to(self, ba_dst, degree=0.5):
        '''
        change the shape, i.e. b/a looks more like `ba_dst` in `degree`

        0<=degree, ba_dst<=1
        if degree == 0, shape would not change
        '''
        if not (0<=ba_dst<=1 and 0<=degree<=1):
            raise Exception('only support 0~1 ba_dst and degree')
        self.ba=degree*ba_dst+(1-degree)*self.ba

    def rounder_shape(self, degree=0.5):
        # make the shape rounder, i.e. b/a is nearer to 1
        self.change_shape_to(1, degree)

    def flatter_shape(self, degree=0.5):
        # make the shape flatter, i.e. b/a is nearer to 0
        self.change_shape_to(0, degree)

    def set_exp_sersic(self):
        # set exponential sersic
        self.n=1

class Expdisk(Model):
    '''
    model sersic
    '''
    # setup for model
    ## valid parameters
    sorted_keys=('1', '2', '3', '4', '9', '10')
    valid_keys=set(sorted_keys)

    ## default parameters
    default_values=[0, 0, 20, 10, 1, 0]

    ## alias of parameters
    alias_keys={
        'x0' : '1',
        'y0' : '2',
        'mag': '3',
        'rs' : '4',
        'ba' : '9',
        'pa' : '10',
    }

    ## comments for parameters
    comments={
        '0' : 'Component type',
        '3' : 'Integrated magnitude',
        '4' : 'R_s (disk scale-length) [pix]',
        '9' : 'Axis ratio (b/a)',
        '10': 'Position angle [deg: Up=0, Left=90]',
    }

    for k in Model.comments:
        if k not in comments:
            comments[k]=Model.comments[k]

    # convert to other model
    def toSersic(self, dest=None, forcep=False):
        if type(dest)==Sersic:
            mod=dest
        elif dest==None:
            mod=Sersic(self.Z)
        else:
            raise Exception('wrong destination type')

        mod._setParamfrom(self, forcep)

        # sequence of call:
        #     __getattr__, __imul__,
        #     __setattr__ with Parameter val
        mod.re*=1.678
        mod.n=1

        return mod

class Edgedisk(Model):
    '''
    model sersic
    '''
    # setup for model
    ## valid parameters
    sorted_keys=('1', '2', '3', '4', '5', '10')
    valid_keys=set(sorted_keys)

    ## alias of parameters
    alias_keys={
        'x0': '1',
        'y0': '2',
        'sb': '3',
        'dh': '4',
        'dl': '5',
        'pa': '10',
    }

    ## comments for parameters
    comments={
        '3' : 'central surface brightness [mag/arcsec^2]',
        '4' : 'disk scale-height [Pixels]',
        '5' : 'disk scale-length [Pixels]',
        '10': 'Position angle [deg: Up=0, Left=90]',
    }

class Nuker(Model):
    '''
    model sersic
    '''
    # setup for model
    ## valid parameters
    sorted_keys=('1', '2', '3', '4', '5', '6', '7', '9', '10')
    valid_keys=set(sorted_keys)

    ## alias of parameters
    alias_keys={
        'x0'   : '1',
        'y0'   : '2',
        'mu'   : '3',
        'rb'   : '4',
        'alpha': '5',
        'beta' : '6',
        'gamma': '7',
        'ba'   : '9',
        'pa'   : '10',
    }

    ## comments for parameters
    comments={
        '3' : 'mu(Rb) [surface brightness mag. at Rb]',
        '4' : 'Rb [pixels]',
        '5' : 'alpha (sharpness of transition)',
        '6' : 'beta (outer powerlaw slope)',
        '7' : 'gamma (inner powerlaw slope)',
        '9' : 'Axis ratio (b/a)',
        '10': 'Position angle [deg: Up=0, Left=90]',
    }

class Devauc(Model):
    '''
    model sersic
    '''
    # setup for model
    ## valid parameters
    sorted_keys=('1', '2', '3', '4', '9', '10')
    valid_keys=set(sorted_keys)

    ## alias of parameters
    alias_keys={
        'x0' : '1',
        'y0' : '2',
        'mag': '3',
        're' : '4',
        'ba' : '9',
        'pa' : '10',
    }

    ## comments for parameters
    comments={
        '3' : 'Integrated magnitude',
        '4' : 'R_e (effective radius) [pix]',
        '9' : 'Axis ratio (b/a)',
        '10': 'Position angle [deg: Up=0, Left=90]',
    }

    # convert to other model
    def toSersic(self, dest=None, forcep=False):
        if type(dest)==Sersic:
            mod=dest
        elif dest==None:
            mod=Sersic(self.Z)
        else:
            raise Exception('wrong destination type')

        mod._setParamfrom(self, forcep)
        mod.n=4

        return mod

class Moffat(Model):
    '''
    model sersic
    '''
    # setup for model
    ## valid parameters
    sorted_keys=('1', '2', '3', '4', '5', '9', '10')
    valid_keys=set(sorted_keys)

    ## alias of parameters
    alias_keys={
        'x0'  : '1',
        'y0'  : '2',
        'mag' : '3',
        'fwhm': '4',
        'pl'  : '5',
        'ba'  : '9',
        'pa'  : '10',
    }

    ## comments for parameters
    comments={
        '3' : 'Integrated magnitude',
        '4' : 'FWHM [Pixels]',
        '5' : 'powerlaw',
        '9' : 'Axis ratio (b/a)',
        '10': 'Position angle [deg: Up=0, Left=90]',
    }

class Ferrer(Model):
    '''
    model sersic
    '''
    # setup for model
    ## valid parameters
    sorted_keys=('1', '2', '3', '4', '5', '6', '9', '10')
    valid_keys=set(sorted_keys)

    ## alias of parameters
    alias_keys={
        'x0'   : '1',
        'y0'   : '2',
        'sb'   : '3',
        'tr'   : '4',
        'alpha': '5',
        'beta' : '6',
        'ba'   : '9',
        'pa'   : '10',
    }

    ## comments for parameters
    comments={
        '3' : 'Central surface brghtness [mag/arcsec^2]',
        '4' : 'Outer truncation radius [pix]',
        '5' : 'Alpha (outer truncation sharpness)',
        '6' : 'Beta (central slope)',
        '9' : 'Axis ratio (b/a)',
        '10': 'Position angle [deg: Up=0, Left=90]',
    }

class Gaussian(Model):
    '''
    model sersic
    '''
    # setup for model
    ## valid parameters
    sorted_keys=('1', '2', '3', '4', '9', '10')
    valid_keys=set(sorted_keys)

    ## alias of parameters
    alias_keys={
        'x0'  : '1',
        'y0'  : '2',
        'mag' : '3',
        'fwhm': '4',
        'ba'  : '9',
        'pa'  : '10',
    }

    ## comments for parameters
    comments={
        '3' : 'Integrated magnitude',
        '4' : 'FWHM [Pixels]',
        '9' : 'Axis ratio (b/a)',
        '10': 'Position angle [deg: Up=0, Left=90]',
    }

class King(Model):
    '''
    model sersic
    '''
    # setup for model
    ## valid parameters
    sorted_keys=('1', '2', '3', '4', '5', '6', '9', '10')
    valid_keys=set(sorted_keys)

    ## alias of parameters
    alias_keys={
        'x0'   : '1',
        'y0'   : '2',
        'mu'   : '3',
        'rc'   : '4',
        'rt'   : '5',
        'alpha': '6',
        'ba'   : '9',
        'pa'   : '10',
    }

    ## comments for parameters
    comments={
        '3' : 'mu(0)',
        '4' : 'Rc',
        '5' : 'Rt',
        '6' : 'alpha',
        '9' : 'Axis ratio (b/a)',
        '10': 'Position angle [deg: Up=0, Left=90]',
    }

class Psf(Model):
    '''
    model sersic
    '''
    # setup for model
    ## valid parameters
    sorted_keys=('1', '2', '3')
    valid_keys=set(sorted_keys)

    ## alias of parameters
    alias_keys={
        'x0'  : '1',
        'y0'  : '2',
        'mag' : '3',
    }

    ## comments for parameters
    comments={
        '3' : 'Integrated magnitude',
    }

class Sky(Model):
    '''
    model sersic
    '''
    # setup for model
    ## valid parameters
    sorted_keys=('1', '2', '3')
    valid_keys=set(sorted_keys)

    fmt_value='%.3e'

    ## alias of parameters
    alias_keys={
        'bkg': '1',
        'dx' : '2',
        'dy' : '3',
    }

    ## comments for parameters
    comments={
        '1' : 'Sky background [ADUs]',
        '2' : 'dsky/dx [ADUs/pix]',
        '3' : 'dsky/dx [ADUs/pix]',
    }

    def is_sky(self):
        return True
