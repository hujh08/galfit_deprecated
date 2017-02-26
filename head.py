#!/usr/bin/env python3

'''
handle head part of galfit template
'''

class Head:
    '''
    class for head of galfit template
    '''
    # setup for head
    ## alias of parameters
    params_alias={
        'input': 'A',
        'output': 'B',
        'sigma': 'C',
        'psf': 'D',
        'psfFactor': 'E',
        'mask': 'F',
        'constraints': 'G',
        'region': 'H',
        'conv': 'I',
        'zerop': 'J',
        'pscale': 'K',
        'disp': 'O',
        'mod': 'P',
    }
    ## alias name for chosen model, i.e. parameter 'P'
    ## 0=optimize, 1=model, 2=imgblock, 3=subcomps
    chosen_name={
        'o': '0',
        'opt': '0',
        'optimize': '0',
        'm': '1',
        'mod': '1',
        'model': '1',
        'b': '2',
        'block': '2',
        'imgblock': '2',
        's': '3',
        'sub': '3',
        'subcomps': '3',
    }
    ## comments for parameters
    params_comments={
        'A': 'Input data image (FITS file)',
        'B': 'Output data image block',
        'C': 'Sigma image',
        'D': 'Input PSF image',
        'E': 'PSF fine sampling factor relative to data',
        'F': 'Bad pixel mask',
        'G': 'File with parameter constraints (ASCII file)',
        'H': 'Image region',
        'I': 'Size for convolution (x y)',
        'J': 'Magnitude photometric zeropoint',
        'K': 'Plate scale (dx dy)   [arcsec per pixel]',
        'O': 'Display type (regular, curses, both)',
        'P': '0=optimize, 1=model, 2=imgblock, 3=subcomps',
    }

    # initiate function
    def __init__(self, params={}, emptyp=True):
        self.__dict__['params']={}
        if not params and emptyp:
            return

        if params:
            if type(params)!=dict:
                raise Exception('expected type: dict, found %s'
                                    % type(params))
            for k in 'ABCDEFGHIJKOP':
                self.params[k]=params[k]
        else:
            for k in 'ABCDFG':
                self.params[k]='none'
            for k in 'IK':
                self.params[k]=['1', '1']
            self.params['E']='1'
            self.params['H']=['1', '2', '1', '2']
            self.params['J']='20'
            self.params['O']='regular'
            self.params['P']='0'

    # update funcitons
    def feedLine(self, line):
        '''
        feed with a line from galfit template
        '''
        fields=line.split()
        key=fields[0][0]
        if key not in 'HIK':
            self.params[key]=fields[1]
        elif key == 'H':
            self.params[key]=fields[1:5]
        else:
            self.params[key]=fields[1:3]

    # functions for more convenient head handle
    def __getattr__(self, prop):
        #print('getattr %s' % prop)
        if prop in Head.params_alias:
            key=Head.params_alias[prop]
            return self.params[key]
        else:
            raise Exception('unsupported property for Head: %s'
                                % prop)
    def __setattr__(self, prop, val):
        #print('setattr: %s' % prop)
        if prop in Head.params_alias:
            key=Head.params_alias[prop]
            if key in 'HIK':
                if type(val)==str:
                    val=val.split()
                elif type(val)!=list:
                    raise Exception('wrong type: expected str/list')

                if key == 'H':
                    if len(val)!=4:
                        raise Exception('wrong value for region')
                else:
                    # for pscale or conv
                    if len(val)!=2:
                        raise Exception('wrong value for region %s'
                                            % prop)
            elif key=='P':
                # special handle mod parameter to allow
                #     giving meaningful model name, like 'block'
                if val in Head.chosen_name:
                    val=Head.chosen_name[val]
                elif val not in '0123':
                    raise Exception('unsupported chosen model')
            self.params[key]=val
        else:
            raise Exception('unsupported property for Head: %s'
                                % prop)

    '''
    # too many property. So switch to setattr
    @property
    def input(self):
        return self.head['A']
    @input.setter
    def input(self, val):
        return self.head['A']=val
    '''

    # function used for print
    def strLines(self):
        lines=[]
        if self.params:
            for k in 'ABCDEFGHIJKOP':
                if k in 'HIK':
                    valstr=" ".join(self.params[k])
                else:
                    valstr=self.params[k]
                lines.append(" %s) %s  # %s" %
                             (k,
                              valstr,
                              Head.params_comments[k]))
        return lines
    def __str__(self):
        return '\n'.join(self.strLines())

