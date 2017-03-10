#!/usr/bin/env python3

'''
cope with standard output file of galfit--fit.log
'''

import re

class FitLogs:

    def __init__(self, filename='fit.log',
                       # start/end number of object,
                       index=None,
                       start=None, end=None):
        self.logs=[]
        self.logsDict={}  # use input and output galfit as key
        with open(filename) as f:
            if (index!=None and index<0) or \
               (start!=None and start<0) or \
               (end!=None and end<0):
                numl=self.numLog(f)
                f.seek(0)

                if index!=None and index<0:
                    index+=numl
                else:
                    if start!=None and start<0:
                        start+=numl
                    if end!=None and end<0:
                        end+=numl
            if index!=None:
                start=index
                end=index+1

            self.feed(f, start, end)

        self.fillDict()

    def numLog(self, iterable):
        '''
        get number of logs
        '''
        num=0
        for line in iterable:
            if line.startswith('Input image     :'):
                num+=1
        return num

    def feed(self, iterable, start=None, end=None):
        # regexp for input image region
        inre=re.compile(r'^(.*)\[(\d+):(\d+),(\d+):(\d+)\]$')
        uncertLine=False
        logNo=0
        skipLog=False
        for line in iterable:
            if line.startswith('Input image     :'):
                nowNo=logNo
                logNo+=1
                if end!=None and nowNo>=end:
                    break
                if start!=None and nowNo<start:
                    skipLog=True
                    continue
                skipLog=False
                val=line.split(':', 1)[1].strip()
                fields=inre.match(val).groups()
                #region=[int(i) for i in fields[1:]]
                lognow=FitLog(fields[0], fields[1:])
                self.logs.append(lognow)
            elif skipLog:
                continue
            elif len(line)>16 and line[16]==':':
                pv=self.linesplit(line)
                lognow.__dict__[pv[0]]=pv[-1]
            elif len(line)>11 and line[11]==':':
                uncertLine=True # next line is uncertainty line

                fields=self.linesplit(line)

                mdname=fields[0]
                mdnow=simpleMod(mdname)
                lognow.models.append(mdnow)

                for s in fields[1:]:
                    mdnow.update(*self.paramParse(s))
            elif uncertLine:
                uncertLine=False
                fields=self.linesplit(line)
                for s in fields:
                    mdnow.uncerts.append(self.paramParse(s)[0])
            elif line.startswith(' Chi^2'):
                clre=re.compile(r'[,=]')
                fields=clre.sub(' ', line).split()
                if len(fields)==2:
                    # reduced chi^2
                    lognow.chisqRed=float(fields[1])
                else:
                    # chi^2
                    lognow.chisq=float(fields[1])
                    lognow.ndof=int(fields[3])

    def fillDict(self):
        for log in self.logs:
            self.logsDict[log.restart]={}
        for log in self.logs:
            self.logsDict[log.restart][log.init]=[]
        for log in self.logs:
            self.logsDict[log.restart][log.init].append(log)

    def paramParse(self, s):
        fit=rel=1
        if s[0] in '[*{':
            val=float(s[1:-1])
            if s[0]=='[':
                fit=0
            elif s[0]=='*':
                rel=0
        else:
            val=float(s)
        return val, fit, rel

    def linesplit(self, line):
        '''
        extract useful information
        '''
        # clear characters (),:
        clre=re.compile(r'[():,\\/]')

        result=clre.sub(' ', line).split()

        if result[0]=='Init.':
            result[0]='init'
        else:
            result[0]=result[0].lower()

        if result[0]=='sky':
            del result[1:4]

        return result

    # more convenient method to access logs
    def __getitem__(self, prop):
        if type(prop)==int:
            return self.logs[prop]
        elif type(prop)==str:
            return self.logsDict[prop]

class FitLog:
    def __init__(self, inputFits, region):
        self.input=inputFits
        self.region=region
        self.models=[]

    # whether the fit result is reliabe
    def reliable(self):
        for mod in self.models:
            if not mod.reliable():
                return False
        return True

class simpleMod:
    '''
    simple model to store parameter from fit.log
    '''
    def __init__(self, name):
        self.name=name
        self.vals=[]
        self.fits=[]
        self.rels=[]
        self.uncerts=[]   # uncertainty
    def update(self, val, fit, rel):
        self.vals.append(val)
        self.fits.append(fit)
        self.rels.append(rel)

    # whether the result of this model is reliable
    def reliable(self):
        for rel in self.rels:
            if not rel:
                return False
        return True
