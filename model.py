#!/usr/bin/env python3

'''
class for galfit supported model
'''

from functools import partial

from .collection import Collection
from .parameter import Parameter
from .containers import Container

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

    def __init__(self, vals=None, fixeds=None, Z=0, id=0):
        super().__init__(Parameter)
        self.__dict__['id']=int(id)
        self.__dict__['Z']=Container(0)
        self.__dict__['name']=self.__class__.__name__.lower()

        self.Z.set(Z)
        if vals!=None:
            self.set_vals(vals)
        if fixeds!=None:
            self.set_fixeds(fixeds)

    # basic methods
    def _get_param(self, key):
        if key=='Z':
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

    # methods to set parameters
    def _gen_set_field(self, vals, field):
        if type(vals)!=dict:
            vals=dict(zip(self.sorted_keys, vals))

        for k in vals:
            getattr(self._get_param(k), 'set_'+field)(vals[k])

    # methods about model
    def get_model_name(self):
        return self.name

    def set_id(self, id):
        self.id=int(id)

    def is_sky(self):
        return False

    def get_xy(self):
        x0s=self._get_param('x0')._str_fields()
        y0s=self._get_param('y0')._str_fields()
        return ' '.join(map(' '.join, zip(x0s, y0s)))

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
               prop == 'Z'

    def __iter__(self):
        return iter([self._get_param(k) for k in self.sorted_keys])

    def __getattr__(self, prop):
        # collect fields, like vals, fixeds
        if prop in {s+'s' for s in Parameter.valid_keys}:
            return [p[prop[:-1]].get() for p in self]

        # methods to set single field, like set_vals, set_frees
        if prop in {'set_'+s+'s' for s in Parameter.valid_keys}:
            return partial(self._gen_set_field, field=prop[4:-1])

        return super().__getattr__(prop)

    def __str__(self):
        keys=('0',)+self.sorted_keys+('Z',)
        specials={'0': self.name}
        if not self.is_sky():
            keys=keys[:2]+keys[3:]
            specials['1']=self.get_xy()
        return self._str(keys, specials=specials)

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

    # convert to other model

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
