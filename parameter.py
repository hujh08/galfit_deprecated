#!/usr/bin/env python3

'''
class for parameters
'''

from functools import partial

from .collection import Collection

class Parameter(Collection):
    '''
    basic class for parameter:
    
    Properties
    ----------
        val: value
        free: free for fit
    '''
    sorted_keys=('val', 'fixed', 'uncert', 'flag')
    valid_keys=set(sorted_keys)

    default_values=[0., 0, -1., 'normal']

    def __init__(self, val=0., fixed=0, uncert=-1., fmt=4):
        super().__init__(fmt=fmt)
        self.set([val, fixed, uncert])

    def keys(self):
        return Parameter.sorted_keys

    def _set_params(self, val):
        if type(val)==str:
            val=val.split()

        if hasattr(val, '__float__'):
            val=[val]
        
        if hasattr(val, '__iter__') and type(val)!=dict:
            val=dict(zip(Parameter.sorted_keys, val))

        for key in val.keys():
            self._set_param(key, val[key])

    # methods of a container
    def get(self):
        return self

    def set(self, val):
        self._set_params(val)

    # chage fixed
    def free(self):
        self.fixed.set(1)

    def frozen(self):
        self.fixed.set(0)

    # magic methods
    def __getattr__(self, prop):
        if prop[:4] in {'set_', 'get_'} and prop[4:] in self.valid_keys:
            # methods, like get_val, set_val
            return partial(getattr(self, '_%s_param' % prop[:3]),
                           prop[4:])
        return super().__getattr__(prop)

    def __getitem__(self, prop):
        return self._get_param(prop)

    def __str__(self):
        return '%-11s %s' % tuple(self._str_fields())

    def _str_fields(self):
        return [str(self._get_param(s)) for s in self.sorted_keys[:2]]
