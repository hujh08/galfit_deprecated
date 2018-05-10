#!/usr/bin/env python3

'''
class for galfit contraint
'''

import re

class Constraints:
    '''
    collection of lines of contraint
    '''
    def __init__(self, fname=None, comps=None):
        self.cons=[]

        if fname!=None:
            self._load_cons(fname, comps)

    def _load_cons(self, fname, comps):
        with open(fname) as f:
            for line in f:
                line=line.strip()
                if not line or line[0]=='#':
                    continue
                cons=Constraint(line, comps)
                self.cons.append(cons)

    def _str(self):
        return '\n'.join(map(str, self.cons))

    def __str__(self):
        return self._str()

class Constraint:
    def __init__(self, line, comps):
        cmtre=re.compile(r'\s*(\S[^#]*?)(\s*$|\s+#)')

        m=cmtre.match(line)
        if not m:
            raise Exception('invalid constraint')

        comp_str, param, type_cons=m.group(1).split(maxsplit=2)

        self.param=param

        # parse component string
        sepre=re.compile(r'\d+(([-_/])\d+)*$')
        m=sepre.match(comp_str)
        if not m:
            raise Exception('invalid components')

        self.sep=sep=m.group(2)
        if sep==None:
            self.sep=''

        comp_ids=[int(i) for i in comp_str.split(sep)]
        self.comps=[comps[i-1] for i in comp_ids]

        # parse constraint type, including its range
        cpars=type_cons.split()
        if len(cpars)==1:
            self.cons_type=cpars[0]   # offset or ratio
        else:
            if len(cpars)==3 and cpars[1]!='to' or len(cpars)>3:
                raise Exception('invalid constraint arguments')

            self.range=[float(cpars[0]), float(cpars[-1])]
            self.cons_type='soft'
            if len(cpars)==3:
                self.cons_type+='_fromto'
            elif self.sep=='/':
                self.cons_type+='_div'
            elif self.sep=='-':
                self.cons_type+='_sub'
            else:
                self.cons_type+='_around'

    def is_soft(self):
        return self.cons_type[:4]=='soft'

    def _str(self):
        comp_ids=[str(comp.id) for comp in self.comps]
        comp_str=self.sep.join(comp_ids)

        if self.is_soft():
            ranges=['%.2f' % i for i in self.range]
            if self.cons_type=='soft_fromto':
                ranges.insert(1, 'to')
            type_str=' '.join(ranges)
        else:
            type_str=self.cons_type

        return '%s %s %s' % (comp_str, self.param, type_str)

    def __str__(self):
        return self._str()




