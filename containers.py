#!/usr/bin/env python3

'''
containers for type of parameters in head and model
'''

# container for single parameter in Head and Parameter
def Container(val, valid={}, alias={}, fmt=None):
    if hasattr(val, '__iter__') and type(val)!=str:
        return Vector(val, fmt)

    if valid:
        return Enum(val, valid, alias, fmt)

    return Scalar(val, fmt)

class Scalar:
    '''
    support int 
    '''
    def __init__(self, val, fmt=None):
        self.val=val

        self.typef=type(val)

        self.strf=str   # used to convert val to string
        if fmt!=None and self.typef==float:
            if type(fmt)==int:
                fmt='%.{}f'.format(fmt)

            if type(fmt)==str:
                fmt=lambda s, fmt=fmt: fmt % s

            if not callable(fmt):
                raise Exception('unsupported format')

            self.strf=fmt

    # copy
    def copy(self):
        newobj=self.__class__(self.val)
        newobj.typef=self.typef
        newobj.strf=self.strf
        return newobj

    def get(self):
        return self.val

    def set(self, val):
        if isinstance(val, Scalar):
            val=val.get()
        self.val=self.typef(val)

    def __str__(self):
        return self.strf(self.val)

    def __getitem__(self, prop):
        return self.val.__getitem__(prop)

    # def __getattr__(self, prop):
    #     return getattr(self.val, prop)

class Enum(Scalar):
    '''
    like enum in scalar with infinite valid value
    '''
    def __init__(self, val, valid={}, alias={}, fmt=None):
        super().__init__(val, fmt)

        self.valid=valid
        self.alias=alias

    def copy(self):
        newobj=super().copy()
        newobj.valid=self.valid.copy()
        newobj.alias=self.alias.copy()
        return newobj

    def set(self, val):
        if val in self.alias:
            val=self.alias[val]

        if val not in self.valid:
            raise Exception('invalid value: %s' % val)

        self.val=val

class Vector(Scalar):
    def __init__(self, val, fmt=None):
        val=list(val)
        super().__init__(val[0], fmt)

        self.val=val
        self.vlen=len(self.val)

    def set(self, val):
        if type(val)==str:
            val=val.split()

        if len(val)!=self.vlen:
            raise Exception('Excepted %i parameters ' % self.vlen +
                            'but got %i ' % len(val))
        self.val[:]=[self.typef(s) for s in val]

    def __setitem__(self, prop, val):
        return self.val.__setitem__(prop, val)

    def __str__(self):
        return ' '.join([self.strf(s) for s in self.val])