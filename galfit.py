#!/usr/bin/env python3

'''
define a class to manage galfit template more conveniently.
and ignore all meaningless parameters, like 7,8 in Sersic model

the main work is to maintain some structures,
    containing informations extracted from and to produce template,
which include:
    head=Head instance: control parameters
    params=[param]: list of parameters,
    comps=[comp]: list of components,
    models={seric:[comp],...}: collect components with same model
    where
        param=Parameter instance:
        comp=Model instance:

about upper/lower case:
    name of head parameters, like A, B, all are upper
    name of models, like sersic, all are lower
    name of parameters, like c0, b1, are lower case
    Z is upper

FUTURE:
    now only handle simple model.
    work for the complicated situation, like C0, Fn, Bn,
        might be implemented in the future if needed
'''
import os
from astropy.io import fits

from .head import Head
from . import model as MODEL
from .model import Model
from .model import Parameter
from .model import getClass

class GalFit:
    '''
    class for a galfit template
    '''
    def __init__(self, filename=None,
                       iterable=None,
                       string=None):
        ## use this syntax to avoid __setarr__
        self.__dict__['params']=[]
        self.__dict__['comps']=[]
        self.__dict__['models']={}
        #self.params=[]
        #self.comps=[]
        #self.models={}

        if filename or iterable or string:
            self.__dict__['head']=Head()
            if filename:
                with open(filename) as f:
                    self.parse(f)
            elif iterable:
                self.parse(iterable)
            else:
                self.parse(string.split('\n'))
        else:
            self.__dict__['head']=Head(emptyp=False)

    # function used to parse lines
    def parse(self, iterable):
        '''
        parse the string to galfit structures
        '''
        ## some regexps
        import re
        ### regexp for head pareameters
        hdre=re.compile(r'^\s*[A-KOP]\)\s+')
        ### regexp for model name, i.e. 0) parameter
        mdre=re.compile(r'^\s*0\)\s+')
        ### regexp for other parameters
        pmre=re.compile(r'^\s*\d+\)\s+')
        ### regexp for skip parameters, i.e. Z
        pzre=re.compile(r'^\s*[zZ]\)\s+')

        ## parse the content line by line
        for line in iterable:
            ### parse head
            if hdre.match(line):
                self.head.feedLine(line)
                continue

            ### parse model name
            if mdre.match(line):
                mdname=line.split()[1]
                mdnow=getClass(mdname)()
                mdname=mdnow.name

                self.comps.append(mdnow)

                if mdname not in self.models:
                    self.models[mdname]=[]
                self.models[mdname].append(mdnow)

                continue

            ### parse parameters
            if pmre.match(line):
                fields=line.split()
                pname=fields[0][:-1]
                if pname not in mdnow.params_req:
                    # skip useless parameter
                    continue
                if pname=='1' and not mdnow.issky():
                    pxv=float(fields[1])
                    pyv=float(fields[2])
                    pxf=int(fields[3])
                    pyf=int(fields[4])

                    param=mdnow.params['1']
                    param.val, param.fit=pxv, pxf

                    param=mdnow.params['2']
                    param.val, param.fit=pyv, pyf
                else:
                    pv=float(fields[1])
                    pf=float(fields[2])
                    param=mdnow.params[pname]
                    param.val, param.fit=pv, pf
                continue

            #### parse Z parameter
            if pzre.match(line):
                zv=int(line.split()[1])
                mdnow.Z=zv
        self.updateParams()

    # functions about head handle
    def __getattr__(self, prop):
        #print('getattr %s' % prop)
        if prop in self.head.params_alias:
            return self.head.__getattr__(prop)
        else:
            raise Exception('unsupported property for GalFit')
    def __setattr__(self, prop, val):
        #print('setattr: %s' % prop)
        if prop in self.head.params_alias:
            self.head.__setattr__(prop, val)
        else:
            raise Exception('unsupported property')

    def __getitem__(self, key):
        '''
        return model if int or slice
               list  if string or slice
        '''
        if type(key)==str:
            return self.models[key]
        elif type(key)==int:
            return self.comps[key]
        else:
            return [self[i] for i in key]
    def __setitem__(self, key, val):
        if type(key)==str:
            self.head.__setattr__(key, val)
        elif type(key)==int:
            self.comps[key].setfrom(val)
        else:
            raise TypeError('unsupported type: %s', type(key))

    # update params list according to comps:
    #     always used after initiate or add/del comp
    def updateParams(self):
        self.params.clear()
        for comp in self.comps:
            for key in comp.params_req:
                self.params.append(comp.params[key])

    # some functions used to add component
    ## given index in comps,
    ##     corresponding starting index in params/models
    def getIndexPM(self, index, mdname=None):
        if mdname==None:
            mdname=self.comps[index].name

        ## index in params
        index_params=0
        ## index in speicified models
        index_models=0
        for comp in self.comps[0:index]:
            index_params+=len(comp.params_req)
            if comp.name==mdname:
                index_models+=1

        return index_params, index_models

    ## general function for add/del comp
    def addComp(self, md, index=0,
                vals=None,fits=None, fixs=None,
                Z=0):
        '''
        add component with model type=md
        values, frees, keeps: list.
            default of frees: 1
        index: insert component before index
            default 0
        '''
        if type(index)!=int:
            raise Exception('only support int for Index')

        if isinstance(md, Model):
            mdAdd=md
        elif type(md)==str or type(md)==type:
            if type(md)==str:
                mdClass=getClass(md)
            else:
                mdClass=md
            mdAdd=mdClass(vals=vals, fits=fits, fixs=fixs,
                          Z=Z, emptyp=False)
        else:
            raise Exception('unsupported type for md')

        mdname=mdAdd.name

        ## index in params/models
        index_param, index_model=self.getIndexPM(index, mdname)

        ## insert to comps
        self.comps.insert(index, mdAdd)

        ## insert to models
        if not mdname in self.models:
            self.models[mdname]=[]
        self.models[mdname].insert(index_model, mdAdd)

        ## update params
        self.params[index_param:index_param]=\
            [mdAdd.params[key] for key in mdAdd.params_req]

    def delComp(self, index=0):
        '''
        index is corresponding to self.comps
        '''
        mdDel=self.comps[index]
        mdname=mdDel.name

        index_param, index_model=self.getIndexPM(index)

        index_pm_end=index_param+len(mdDel.params_req)

        del self.comps[index]
        del self.params[index_param:index_pm_end]
        del self.models[mdname][index_model]

        if not self.models[mdname]:
            del self.models[mdname]

        return mdDel

    def delCompMod(self, mdname, index=0):
        '''
        delete component of specified model
        '''
        mdname=mdname.lower()
        if not mdname in self.models:
            print("no model %s found\n" % mdname)
            return

        mdDel=self.models[mdname][index]

        ## index in self.comps
        index_comp=0
        ## index in self.parameters
        index_param=0
        for comp in self.comps:
            if comp is mdDel:
                break
            index_comp+=1
            index_param+=len(comp.params_req)
        index_pm_end=index_param+len(mdDel.params_req)

        del self.comps[index_comp]
        del self.params[index_param:index_pm_end]
        del self.models[mdname][index]

        if len(self.models[mdname])==0:
            del self.models[mdname]

        return mdDel

    ### frequently used function
    def push(self, md, *args, **keys):
        self.addComp(md, len(self.comps), *args, **keys)
    def pop(self):
        return self.delComp(-1)

    def shift(self, md, *args, **keys):
        self.addComp(md, 0, *args, **keys)
    def unshift(self):
        return self.delComp(0)

    def popMod(self, mdname):
        return self.delCompMod(mdname, -1)
    def unshiftMod(self, mdname):
        return self.delCompMod(mdname, 0)

    ### handle specific model
    def addSersic(self, *args, **keys):
        self.addComp(MODEL.Sersic, len(self.comps), *args, **keys)

    def addSky(self, *args, **keys):
        self.addComp(MODEL.Sky, len(self.comps), *args, **keys)

    # functions to handle all fit/fix state of parameters
    def setfit(self, fit=1):
        for param in self.params:
            param.setfit(fit)
    def setfix(self, fix=1):
        for param in self.params:
            param.setfix(fix)

    ## frequently used function
    def fit(self):
        self.setfit()
    def fix(self):
        self.setfix()

    def unfit(self):
        self.setfit(0)
    def unfix(self):
        self.setfix(0)

    # split sersic to 2 sersic
    def sersicSplit(self, ind):
        #  sersic0: bulge, sersic1: disk
        sersic1=self[ind]
        sersic1.mag+=0.30102999566398114  # plus log10(2)
        sersic0=sersic1.copy()

        self.addComp(sersic0, ind)

        # update parameters
        sersic0.re*=0.5
        sersic1.re*=1.5

        sersic0.n=4
        sersic1.n=1

        sersic0.ba=0.8

    # handle parameters in models
    def xyshift(self, xshift, yshift):
        for comp in self.comps:
            if not comp.issky():
                comp.x0+=xshift
                comp.y0+=yshift

    # fitsname
    def get_fitsNameID(self):
        fitsname=self.input
        if fitsname[-1]==']':
            fitsname, hduid=fitsname[:-1].split('[')
            hduid=int(hduid)
        else:
            hduid=0
        return fitsname, hduid

    def get_fitsHead(self):
        return fits.getheader(*self.get_fitsNameID())

    # about head parameters
    def confirm_region(self):
        fhead=self.get_fitsHead()
        nx=fhead['NAXIS1']
        ny=fhead['NAXIS2']
        region=self.region
        if region[1]>nx:
            region[1]=nx
        if region[3]>ny:
            region[3]=ny

    # method to set head
    def bindcons(self, cons, name='contstraints'):
        with open(name, 'w') as f:
            for l in cons:
                f.write(l+'\n')
        self.constraints=name

    # functions to print information
    def strLines(self):
        lines=['==============================================',
               '# IMAGE and GALFIT CONTROL PARAMETERS']
        lines.extend(self.head.strLines())
        lines.append('')
        lines.append('# INITIAL FITTING PARAMETERS')
        lines.append('#')
        lines.append('#   For component type, the allowed functions:')
        lines.append('#     sersic, expdisk, edgedisk, devauc,')
        lines.append('#     king, nuker, psf, gaussian, moffat,')
        lines.append('#     ferrer, and sky.')
        lines.append('#')
        lines.append('#   Hidden parameters appear only when specified:')
        lines.append('#     Bn (n=integer, Bending Modes).')
        lines.append('#     C0 (diskyness/boxyness),')
        lines.append('#     Fn (n=integer, Azimuthal Fourier Modes).')
        lines.append('#     R0-R10 (coordinate rotation, for spiral).')
        lines.append('#     To, Ti, T0-T10 (truncation function).')
        lines.append('#')
        lines.append('# --------------------------------------------')
        lines.append('#   par)    par value(s)    fit toggle(s)')
        lines.append('# --------------------------------------------')
        lines.append('')

        compNo=1
        for comp in self.comps:
            lines.append('# Component number: %i' % compNo)
            lines.extend(comp.strLines())
            lines.append('')
            compNo+=1

        lines.append('==============================================')

        return lines

    def __str__(self):
        return '\n'.join(self.strLines())

    def __repr__(self):
        return self.__str__()

    def write(self, output=None, backup=False):
        '''
        convert the structures to template file
        '''
        import sys, os
        if type(output)==str:
            if backup and os.path.isfile(output):
                from backupKit import uniqName
                output_bk=uniqName(output)
                os.rename(output, output_bk)

            f=open(output, 'w')
        elif output==None:
            f=sys.stdout
        else:
            f=output

        f.write(self.__str__())
        f.write('\n')

        if type(output)==str:
            f.close()