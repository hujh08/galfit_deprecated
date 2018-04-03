#!/usr/bin/env python3

'''
collection of containers
    which is super class of Head, Model and Parameter
'''

from .containers import Container

class Collection:

    # some class properties
    sorted_keys=''
    valid_keys=set()

    alias_keys={}

    default_values=()

    fmt_value=None
    len_valstr=1
    len_keystr=1

    valid_values={}  # each item is a list with 2 elements at most

    comments={}

    def __init__(self, container=Container, fmt=None):
        default_values=self.default_values
        if type(default_values)!=dict:
            default_values=dict(zip(self.sorted_keys, self.default_values))

        if fmt==None:
            fmt=self.fmt_value

        # collect containers in a dict
        self.__dict__['params']={}
        for k in self.valid_keys:
            self.params[k]=container(default_values[k],
                                     *self.valid_values.get(k, []),
                                     fmt=fmt)

    def _get_param(self, key):
        if key in self.alias_keys:
            key=self.alias_keys[key]

        if key not in self.valid_keys:
            raise AttributeError(key)

        return self.params[key]

    def _set_param(self, key, val):
        '''
        basic interface to set parameters
        '''
        self._get_param(key).set(val)

    def _get_comments(self, key):
        comments=self.comments
        if key not in comments:
            # if super(), means super(__class__, self)
            #     where __class__ is Collection
            #sup=super(self.__class__, )
            sup=self.__class__.__bases__[0]
            if issubclass(sup, Collection):
                comments=sup.comments
        return comments.get(key, '')

    def _str(self, keys=None, vlen=None, klen=None, specials={}):
        if keys==None:
            keys=self.sorted_keys
        if vlen==None:
            vlen=self.len_valstr
        if klen==None:
            klen=self.len_keystr
            
        lines=[]
        for k in keys:
            v=specials[k] if k in specials else self._get_param(k)
            c=self._get_comments(k)

            lines.append('%*s) %-*s # %s' % (klen, k, vlen, v, c))
        return '\n'.join(lines)

    def __str__(self, specials={}):
        return self._str(specials=specials)

    # magic methods
    def __contains__(self, prop):
        if prop in self.valid_keys or prop in self.alias_keys:
            return True
        return False

    def __getattr__(self, prop):
        return self._get_param(prop).get()

    # def __getitem__(self, prop):
    #     return self._get_param(prop)
