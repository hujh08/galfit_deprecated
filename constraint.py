#!/usr/bin/env python3

'''
    Module to handle constraint file
'''

import re

from collection import is_str_type

class Constraints:
    '''
        class to represent a constraint file
            that is collection of serveral constraint rules,

        A constraint rule in the collection is represented by class `ConsRule`
    '''
    def __init__(self, fname=None):
        '''
            initiation

            it could be initiated as empty, if `fname` is None
                or to load a constraint file

            Parameter
                fname: None, or str
                    for str, if it is 'none', same as None
        '''
        self.rules_cons=[]   # collection of constraints

        assert fname is None or is_str_type(fname)

        if is_str_type(fname) and fname!='none':
            self.load_file(fname)

    def load_file(self, fname):
        '''
            load a constraint file
        '''
        with open(fname) as f:
            for line in f:
                line=line.strip()
                if (not line) or line[0]=='#':
                    continue
                self.add_cons_from_line(line)

    ## add method
    def add_cons_from_line(self, line):
        '''
            add a constraint rule from a line,
                with format in galfit constraint file
        '''
        cons=ConsRule(line)
        self.rules_cons.append(cons)

    # stringlizing
    def __str__(self):
        '''
            user-friendly string
        '''
        return '\n'.join(map(str, self.rules_cons))

    def writeto(self, fname):
        '''
            write to a file
        '''
        with open(fname, 'w') as f:
            f.write(str(self)+'\n')

class ConsRule:
    '''
        class for one constraint rule

        6 types of constraint
            hard, offset: e.g. '1_2_3   x   offset'
                keep x1-x2, x2-x3 fixed during fitting
                    x1,x2,x3 for parameter x of components 1,2,3
                often used for position parameters, like center x, y

            hard, ratio: e.g. '1_2_3   r   ratio'
                keep r1/r2, r2/r3 fixed during fitting
                often used for positive parameters, like re, ba

            soft, fromto range: e.g. '1    n   v1 to v2'
                keep n1 within values from v1 to v2
                often used for values having empirical range, like sersic index

            soft, shift range: e.g. '1    x   d1  d2'
                keep shift x within range from v1 to v2
                    that is, assume x0 now,
                        then x must be from x0+d1 to x0+d2 during fitting
                often used for values having a varing range

            soft, offset range: e.g. '1-2    x    v1 v2'
                keep x1-x2 within values from v1 to v2

            soft, ratio range: e.g. '1/2    r    t1 t2'
                keep r1/r2 within values from v1 to v2
    '''
    # re pattern
    fmt_ptn=r'^\s*(%s)\s+([a-zA-Z\d]+)\s+(%s)(?:\s*$|\s+#)'

    ## hard offest
    fmt_comps=r'\d+_\d+(?:_\d+)*'
    ptn_offset=re.compile(fmt_ptn % (fmt_comps, 'offset'))

    ## hard ratio
    ptn_ratio=re.compile(fmt_ptn % (fmt_comps, 'ratio'))

    ## soft, from to: v1 to v2, constraining values within v1 to v2
    fmt_flt=r'[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?'  # float
    fmt_cons_to=r'({0})\s+to\s+({0})'.format(fmt_flt)
    ptn_fromto=re.compile(fmt_ptn % (r'\d+', fmt_cons_to))

    ## soft, shift: v1 v2, (current v), constraining values v+v1 to v+v2
    fmt_cons_range=r'({0})\s+({0})'.format(fmt_flt)
    ptn_shift=re.compile(fmt_ptn % (r'\d+', fmt_cons_range))

    ## soft, offset: p1-p2 x v1 v2
    ptn_soft_offset=re.compile(fmt_ptn % (r'\d+-\d+', fmt_cons_range))

    ## soft, ratio: p1/p2 x v1 v2
    ptn_soft_ratio=re.compile(fmt_ptn % (r'\d+/\d+', fmt_cons_range))

    ### collections of pattern
    ptns_cons=dict(
        hard_offset=ptn_offset,
        hard_ratio=ptn_ratio,
        soft_fromto=ptn_fromto,
        soft_shift=ptn_shift,
        soft_offset=ptn_soft_offset,
        soft_ratio=ptn_soft_ratio,
    )

    # constraint type
    types_cons=set(ptns_cons.keys())

    # seperation of components: mainly used for output
    seps_cons=dict(
        hard_offset='_',
        hard_ratio='_',
        soft_fromto='',
        soft_shift='',
        soft_offset='-',
        soft_ratio='/',
    )

    def __init__(self, line=None):
        '''
            3 properties for a constraint rule
                comps: components containing parameters with constraint
                par: parameter with constraint
                type: constraint type

            it could be initiated by a line in constraint file
        '''
        self.comps=None
        self.par=None
        self.vals=None   # values of constraint

        if line is not None:
            self.load_line(line)

    def load_line(self, line):
        '''
            load a line in constraint file
        '''
        line=line.strip()

        if (not line) or line[0]=='#':
            return

        for t, ptn in self.ptns_cons.items():
            m=ptn.match(line)
            if m:
                break

        if not m:
            return

        comps, par, *vals=m.groups()
        self.par=par

        s=self.seps_cons[t]
        if s:
            self.comps=[int(i) for i in comps.split(s)]
        else:
            self.comps=[int(comps)]

        if t.startswith('hard_'):
            self.vals=(t,)
        else:
            self.vals=(t, *[float(i) for i in vals[-2:]])

    # stringlizing
    def __str__(self):
        '''
            string of the constraint rule
        '''
        fmt='%s    %s    %s' # format of the string

        # parameter
        par=self.par

        # componentss
        t=self.vals[0]
        comps=self.seps_cons[t].join(map(str, self.comps))

        # constraint values
        if t.startswith('hard_'):
            vals=t[len('hard_'):]
        else:
            if t=='soft_fromto':
                fmt_v='%g to %g'
            else:
                fmt_v='%g %g'
            vals=fmt_v % tuple(self.vals[-2:])

        return fmt % (comps, par, vals)


