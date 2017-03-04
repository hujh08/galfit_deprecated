#!/usr/bin/env python3

'''
class for model supported by galfit,
including:
    sersic
    sky
'''

from .parameter import Parameter

mod_support={
    'Nuker', 'Devauc', 'Psf', 'King',
    'Gaussian', 'Edgedisk', 'Sersic',
    'Moffat', 'Ferrer', 'Expdisk', 'Sky',
}

#from string import capitalize
# work in python2, fail python3
#def getClassname(name):
#    return '%s%s' % (name[0].upper(), name[1:].lower())

def getClass(name):
    classname=name.capitalize()
    if classname not in mod_support:
        raise Exception('unsupported model: %s' % classname)
    #print(classname)
    return globals()[classname]

class Model:
    '''
    basic class for model class
    '''
    # default parameters for all model
    # some model, like Sersic, may specify this property
    params_default=[0]*10
    def __init__(self, vals=None, Z=0,
                       fits=None, fixs=None,
                       emptyp=True):
        self.__dict__['name']=self.__class__.__name__.lower()
        self.__dict__['Z']=Z
        self.__dict__['params']={}

        self.setparams(vals, fits, fixs)

    # deep copy of model
    def copy(self):
        p=self.__class__(Z=self.Z)
        p._setParamfrom(self)
        return p

    def copyto(self, mod, force=False, forcep=False):
        # forcep: force to change fit of parameters
        if self is mod:
            return
        if not force and self.name != mod.name:
            raise Exception('inconsistent model: from %s to %s' %
                                (self.name.capitalize(), 
                                 mod.name.capitalize()))
        elif self.name != mod.name:
            # force and self.name != mod.name
            convAttr='to%s' % mod.name.capitalize()
            #print(convAttr)
            convFunc=getattr(self, convAttr)
            convFunc(self, mod, forcep)
        else:
            # self.name == mod.name
            mod.Z=self.Z
            mod._setParamfrom(self, forcep)

    def setfrom(self, mod, force=False, forcep=False):
        mod.copyto(self, force, forcep)

    def _setParamfrom(self, mod, forcep=False):
        # not check the match of type
        #     so be careful to use this function
        for key, param in self.params.items():
            param.setfrom(mod.params[key], forcep)

    # set parameters
    def setparams(self, vals=None, fits=None, fixs=None):
        for key, val in zip(self.params_req, self.valIter(vals)):
            self.params[key]=Parameter(val)

        if fits!=None or fits!=1:
            for key, fit in zip(self.params_req,
                                self.valIter(fits, 'fit')):
                self.params[key].fit=fit
        if fixs!=None or fixs!=0:
            for key, fix in zip(self.params_req,
                                self.valIter(fits, 'fix')):
                self.params[key].fix=fix

    def valIter(self, vals=None, mod='val'):
        '''
        this also works for fits and fixs
        '''
        result=[]
        l=len(self.params_req)
        if hasattr(vals, '__iter__'):
            if len(vals)<l:
                raise Exception('no enough arguments for %s' % mod)
            if type(vals)==dict:
                for key in self.params_req:
                    result.append(vals[key])
            else:
                return vals
        elif vals==None:
            if mod=='val':
                result=self.params_default
            elif mod=='fit':
                result=[1]*l
            elif mod=='fix':
                result=[0]*l
            else:
                raise Exception('unsupported mod for valIter: %s'
                                    % mod)
        elif type(vals)==int or type(vals)==float:
            result=[vals]*l
        return result

    # support alias name of parameters
    def getParamKey(self, key):
        '''
        convert kinds key, like 're', 1, '1', to key in self.params
        '''
        if key in self.params_req:
            return key
        elif key in self.params_alias:
            return self.params_alias[key]
        else:
            return None

    def __getitem__(self, key):
        '''
        get parameters
        '''
        if type(key)==int:
            return self.params[self.params_req[key]]
        elif type(key)==str:
            return self.params[self.getParamKey(key)]
        else:
            return [self[i] for i in key]
    def __setitem__(self, key, val):
        self[key].setfrom(val)

    def __getattr__(self, prop):
        #print('getattr: %s' % prop)
        key=self.getParamKey(prop)
        if key!=None:
            return self.params[key]
        elif prop[:2]=='to':
            raise Exception('unconvertible from %s to %s' %
                                (self.__class__.__name__, prop[2:]))
        else:
            raise Exception('unsupported alias %s for %s' %
                                (prop, self.name))

    def __setattr__(self, prop, val):
        #print('setattr: %s' % prop)
        key=self.getParamKey(prop)
        if key!=None:
            if key not in self.params:
                self.params[key]=Parameter()

            self.params[key].setfrom(val)

        elif prop=='Z':
            # even existing attribution can call for this funciton
            # unlike __getattr__
            self.__dict__['Z']=val
        else:
            raise Exception('unsupported alias for %s' % self.name)

    # cope with fit/fix state
    def setfit(self, fit=1):
        for param in self.params.values():
            param.setfit(fit)
    def setfix(self, fix=1):
        for param in self.params.values():
            param.setfix(fix)

    ## frequently used functions
    def fit(self):
        self.setfit()
    def fix(self):
        self.setfit()

    def unfit(self):
        self.setfit(0)
    def unfix(self):
        self.setfit(0)

    # sky model has different format to print
    def issky(self):
        return isinstance(self, Sky)

    # used to print
    def strLines(self):
        lines=[]
        lines.append(" 0) %s    # Component type" % self.name)
        params_req=self.params_req
        if not self.issky():
            params_req=params_req[2:]
            xp=self.params['1']
            yp=self.params['2']
            lines.append(" 1) %f %f %i %i # Position x, y" %
                         (xp.val, yp.val, xp.fit, yp.fit))

        for key in params_req:
            p=self.params[key]
            comment=self.params_comments[key]
            lines.append("%2s) %f %i     # %s" %
                         (key, p.val, p.fit, comment))
        ## handle Z
        lines.append(" Z) %i # Skip this model? (yes=1, no=0)" %
                     self.Z)

        return lines

    def __str__(self):
        return '\n'.join(self.strLines())

class Sersic(Model):
    '''
    model sersic
    '''
    # setup for model
    ## required parameters
    params_req=('1', '2', '3', '4', '5', '9', '10')
    ## default parameters
    params_default=[0, 0, 20, 10, 2, 1, 0]
    ## alias of parameters
    params_alias={
        'x0' : '1',
        'y0' : '2',
        'mag': '3',
        're' : '4',
        'n'  : '5',
        'ba' : '9',
        'pa' : '10',
    }
    ## comments for parameters
    params_comments={
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
    ## required parameters
    params_req=('1', '2', '3', '4', '9', '10')
    ## default parameters
    params_default=[0, 0, 20, 10, 1, 0]
    ## alias of parameters
    params_alias={
        'x0' : '1',
        'y0' : '2',
        'mag': '3',
        'rs' : '4',
        'ba' : '9',
        'pa' : '10',
    }
    ## comments for parameters
    params_comments={
        '3' : 'Integrated magnitude',
        '4' : 'R_s (disk scale-length) [pix]',
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
    ## required parameters
    params_req=('1', '2', '3', '4', '5', '10')
    ## alias of parameters
    params_alias={
        'x0': '1',
        'y0': '2',
        'sb': '3',
        'dh': '4',
        'dl': '5',
        'pa': '10',
    }
    ## comments for parameters
    params_comments={
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
    ## required parameters
    params_req=('1', '2', '3', '4', '5', '6', '7', '9', '10')
    ## alias of parameters
    params_alias={
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
    params_comments={
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
    ## required parameters
    params_req=('1', '2', '3', '4', '9', '10')
    ## alias of parameters
    params_alias={
        'x0' : '1',
        'y0' : '2',
        'mag': '3',
        're' : '4',
        'ba' : '9',
        'pa' : '10',
    }
    ## comments for parameters
    params_comments={
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
    ## required parameters
    params_req=('1', '2', '3', '4', '5', '9', '10')
    ## alias of parameters
    params_alias={
        'x0'  : '1',
        'y0'  : '2',
        'mag' : '3',
        'fwhm': '4',
        'pl'  : '5',
        'ba'  : '9',
        'pa'  : '10',
    }
    ## comments for parameters
    params_comments={
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
    ## required parameters
    params_req=('1', '2', '3', '4', '5', '6', '9', '10')
    ## alias of parameters
    params_alias={
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
    params_comments={
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
    ## required parameters
    params_req=('1', '2', '3', '4', '9', '10')
    ## alias of parameters
    params_alias={
        'x0'  : '1',
        'y0'  : '2',
        'mag' : '3',
        'fwhm': '4',
        'ba'  : '9',
        'pa'  : '10',
    }
    ## comments for parameters
    params_comments={
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
    ## required parameters
    params_req=('1', '2', '3', '4', '5', '6', '9', '10')
    ## alias of parameters
    params_alias={
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
    params_comments={
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
    ## required parameters
    params_req=('1', '2', '3')
    ## alias of parameters
    params_alias={
        'x0'  : '1',
        'y0'  : '2',
        'mag' : '3',
    }
    ## comments for parameters
    params_comments={
        '3' : 'Integrated magnitude',
    }

class Sky(Model):
    '''
    model sersic
    '''
    # setup for model
    ## required parameters
    params_req=('1', '2', '3')
    ## alias of parameters
    params_alias={
        'bkg': '1',
        'dx' : '2',
        'dy' : '3',
    }
    ## comments for parameters
    params_comments={
        '1' : 'Sky background [ADUs]',
        '2' : 'dsky/dx [ADUs/pix]',
        '3' : 'dsky/dx [ADUs/pix]',
    }