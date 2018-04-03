#!/usr/bin/env python3

'''
cope with standard output file of galfit--fit.log
'''

import re

from .tools import gfname

# # convert template file number to its name
# def gfname(num):
#     return 'galfit.%02i' % num

class FitLogs:
    def __init__(self, filename='fit.log'):
        self.logs=[]

        self._load_file(filename)

    def _load_file(self, filename):
        with open(filename) as f:
            log=FitLog()
            for line in f:
                line=line.rstrip()
                if not line or line=='-'*77:
                    continue
                
                key, *fields=line.split(':', maxsplit=1)
                if len(key)==16:
                    key='_'.join([s.lower() for s in key.split()])
                    key=key.replace('.', '')
                    val=fields[0].strip()

                    if key=='input_image':
                        log=FitLog(val)
                        self.logs.append(log)
                    else:
                        log[key]=val
                elif line.startswith(' Chi^2'):
                    for eqstr in line.split(','):
                        log._set_chi_fromlog(eqstr)
                else:
                    log.append_lines(line)

    def parse_all(self):
        for log in self.logs:
            log._parse_lines()

    def _get_log(self, logs, ind):
        if not logs:
            raise Exception('no log found')

        log=logs[ind]
        if not hasattr(log, 'mods'):
            log._parse_lines()
        return log

    def get_log(self, *args, ind=-1):
        if not args:
            return self.get_log_index(ind)

        if len(args)==1:
            return self.get_log_result(*args, ind)

        if len(args)==2:
            return self.get_log_init_result(*args, ind)

        if len(args)==3:
            return self.get_log_init_result(*args)

        raise Exception('expect 3 positional arguments at most, '+
                        'but were given %i' % len(args))

    def get_log_index(self, ind):
        return self._get_log(self.logs, ind)

    def get_log_init(self, init, ind=-1):
        if type(init)==int:
            init=gfname(init)
        logs=[l for l in self.logs if l.init_file==init]
        return self._get_log(logs, ind)

    def get_log_result(self, result, ind=-1):
        if type(result)==int:
            result=gfname(result)
        logs=[l for l in self.logs if l.result_file==result]
        return self._get_log(logs, ind)

    def get_log_init_result(self, init, result, ind=-1):
        if type(init)==int:
            init=gfname(init)
        if type(result)==int:
            result=gfname(result)

        logs=[l for l in self.logs
                    if l.init_file==init and l.result_file==result]
        return self._get_log(logs, ind)

class FitLog:
    '''
    container for log of one galfit
    '''
    def __init__(self, input_image='', output_image='',
                       init_file='', result_file=''):
        self.input_image=input_image
        self.output_image=output_image
        self.init_file=init_file
        self.result_file=result_file

        self.lines=[]
        #self.mods=[]

    def append_lines(self, line):
        self.lines.append(line)

    def _set_chi_fromlog(self, eqstr):
        key, val=[i.strip() for i in eqstr.split('=')]
        if key=='Chi^2':
            self.chisq=float(val)
        elif key=='ndof':
            self.ndof=int(val)
        elif key=='Chi^2/nu':
            self.reduce_chisq=float(val)
        else:
            raise Exception('unexpected key for chi: %s' % key)

    def _parse_lines(self):
        lines=self.lines
        self.mods=[]
        for vals, uncerts in zip(lines[0::2], lines[1::2]):
            self.mods.append(LogMod(vals, uncerts))

    def __setitem__(self, prop, val):
        if prop=='init_par_file':
            prop='init_file'
        elif prop=='restart_file':
            prop='result_file'
        setattr(self, prop, val)

class LogMod:
    def __init__(self, *lines, name=''):
        self.name=name
        self.vals=[]
        self.uncerts=[]
        self.flags=[]

        if lines:
            self._parse_lines(*lines)

    def _parse_lines(self, vals, uncerts):
        self._parse_vals(vals)
        self._parse_uncerts(uncerts)

        if not len(self.vals)==len(self.uncerts)==len(self.flags):
            raise Exception('mismatch of number after line-parse')

    def _parse_vals(self, line):
        name, vals=line.split(':', maxsplit=1)
        self.name=name.strip().lower()

        for field in vals.split():
            val, flag=self._parse_item(field)
            if val==None:
                continue
            self.vals.append(val)
            self.flags.append(flag)

        if self.name=='sky':
            self.vals[:2]=[]
            self.flags[:2]=[]

    def _parse_uncerts(self, line):
        for field in line.split():
            val, flag=self._parse_item(field)
            if val==None:
                continue
            self.uncerts.append(val)

    def _parse_item(self, val):
        ends='][()*,'
        pattern=r'^([{0}]*)([^{0}]*)([{0}]*)$'.format(ends)
        m=re.match(pattern, val)
        if not m:
            return None, None

        groups=m.groups()
        if not groups[1]:
            return None, None

        val=float(groups[1])

        flag='normal'
        head, tail=groups[0], groups[2]
        if head and tail:
            mark=head[-1]+tail[0]
            if mark=='**':
                flag='unreliable'
            elif mark=='[]':
                flag='fixed'
            elif mark=='{}':
                flag='constrainted'

        return val, flag
