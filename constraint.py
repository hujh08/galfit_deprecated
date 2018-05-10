#!/usr/bin/env python3

'''
class for galfit contraint
'''

import re

class Constraints:
    '''
    collection of lines of contraint
    '''
    paramre=re.compile(r'x|y|mag|re')
    def __init__(self, comps, fname=None):
        self.comps=comps
        self.cons=[]

        if fname!=None:
            self._load_file(fname, comps)

    def _load_file(self, fname):
        with open(fname) as f:
            for line in f:
                line=line.strip()
                if not line or line[0]=='#':
                    continue
                self.add_cons(line)

    def _str(self):
        return '\n'.join(map(str, self.cons))

    # user methods
    def is_empty(self):
        return not self.cons

    ## add/remove constraints
    def clear(self):
        self.cons.clear()

    def add_cons(self, *args):
        if len(args)==1:
            cons=Constraint(self.comps, *args)
            self.cons.append(cons)
        else:
            comp_ids, params=args[:2]
            if type(params)==str:
                params=params.split()
                if len(params)==1:
                    params=self.paramre.findall(params[0])
            for p in params:
                cons=Constraint(self.comps, comp_ids, p, *args[2:])
                self.cons.append(cons)

    ## output
    def write(self, fname):
        with open(fname, 'w') as f:
            f.write(self._str()+'\n')

    def __str__(self):
        return self._str()

class Constraint:
    sep_cons={
        'offset': '_',
        'ratio': '_',
        'soft_fromto': '',
        'soft_around': '',
        'soft_sub': '-',
        'soft_div': '/'
    }

    def __init__(self, comps, *args, **kwargs):
        if len(args)==1:
            self._load_line(comps, *args)
        else:
            self._from_fields(comps, *args, **kwargs)

    def _from_fields(self, comps, *args, **kwargs):
        if len(args)<2 or len(args)>3:
            raise Exception('expect 2 or 3 arguments, but got %i'
                                    % len(args))

        cpids, self.param=args[:2]

        # parse component string
        sep=''
        if len(comps)<10:  # like matplotlib
            if type(cpids)==int and cpids>10:
                cpids=str(cpids)
            if type(cpids)==str and re.match(r'[1-9]+$', cpids):
                cpids=[int(i) for i in cpids]
        if type(cpids)==int:
            cpids=[cpids]
        if type(cpids)==str:
            cpids, sep=self._parse_comp(cpids)

        self.comps=[comps[i-1] for i in cpids]

        # parse constraint type
        if sep not in '-/':
            if len(args)!=3:
                raise Exception('unknown constraint type')
        elif len(args)==2:
            crange=kwargs['range']
            if sep=='/':
                cons_type='soft_div'
            else:
                cons_type='soft_sub'
        else:
            cons_type, crange=self._parse_type(args[2], sep, **kwargs)

        self.cons_type=cons_type
        if cons_type not in {'offset', 'ratio'}:
            self.range=crange
        
        self.sep=self._get_sep(cons_type)

    def _load_line(self, comps, line):
        cmtre=re.compile(r'\s*(\S[^#]*?)(\s*$|\s+#)')

        m=cmtre.match(line)
        if not m:
            raise Exception('invalid constraint')

        comp_str, param, type_cons=m.group(1).split(maxsplit=2)

        self.param=param

        # parse component string
        comp_ids, sep=self._parse_comp(comp_str)
        if sep and sep==' ':
            raise Exception('invalid components')

        self.sep=sep
        self.comps=[comps[i-1] for i in comp_ids]

        # parse constraint type, including its range
        self.cons_type, self.crange=self._parse_type(type_cons, sep)

    def _parse_comp(self, comps):
        comps=comps.strip()

        sepre=re.compile(r'\d+(([-_/]+)\d+)*$')
        m=sepre.match(comps)
        if m:
            sep=m.group(2)
            if sep==None:
                sep=''
                comp_ids=[int(comps)]
            else:
                comp_ids=[int(i) for i in comps.split(sep)]
            return comp_ids, sep

        comp_ids=[int(i) for i in comps.split()]
        return comp_ids, ' '

    def _parse_type(self, ctype, sep, **kwargs):
        cpars=ctype.split()
        if len(cpars)==1:
            cons_type=cpars[0]   # offset or ratio
            crange=None
            if cons_type not in {'offset', 'ratio'}:
                crange=kwargs['range']
        else:
            if len(cpars)==3 and cpars[1]!='to' or len(cpars)>3:
                raise Exception('invalid constraint arguments')

            crange=[float(cpars[0]), float(cpars[-1])]
            cons_type='soft'
            if len(cpars)==3:
                if sep!='':
                    raise Exception('unexcepted component sep')
                cons_type+='_fromto'
            elif sep=='/':
                cons_type+='_div'
            elif sep=='-':
                cons_type+='_sub'
            elif sep=='':
                cons_type+='_around'
            else:
                raise Exception('unexcepted component sep')
        return cons_type, crange

    def _get_sep(self, ctype):
        return self.sep_cons[ctype]

    # user methods
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




