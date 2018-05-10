#!/usr/bin/env python3

'''
class of template's head, which contains head parameters A-P
'''

from .collection import Collection

class Head(Collection):
    '''
    class to hold head parameters A-P
    '''

    # setup for head
    ## valid parameters
    sorted_keys='ABCDEFGHIJKOP'
    valid_keys=set(sorted_keys)

    ## alias of parameters
    alias_keys={
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

    ## default parameters
    default_values={
        # Attention:
        #   type of value will be maintained during changing
        'A': 'none',
        'B': 'none',
        'C': 'none',
        'D': 'none',
        'E': 1,   # can only be an integer, see readme of galfit
        'F': 'none',
        'G': 'none',
        'H': [0, 0, 0, 0],
        'I': [0, 0],
        'J': 20.,
        'K': [1.0, 1.0],
        'O': 'regular',
        'P': '0',
    }

    fmt_value=3  # precise
    len_valstr=19  # length of string of value

    ## valid galfit mode parameters
    valid_mod=set('012')

    ## alias name for galfit mode, that is, parameter 'P'
    ## 0=optimize, 1=model, 2=imgblock, 3=subcomps
    alias_mod={
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

    ## valid display mode
    valid_disp={'regular', 'curses', 'both'}

    valid_values={
        'O': [valid_disp],
        'P': [valid_mod, alias_mod]
    }

    ## comments for parameters
    comments={
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

    # methods of construction
    ## basic interface of parameters

    def _feed_key_fields(self, key, fields):
        '''
        feed in fields in a line seperated by whitespace
            except the 1st field,
                which is offered as key after removing the last ')'
        '''
        if key in 'IK':
            val=fields[:2]
        elif key=='H':
            val=fields[:4]
        else:
            val=fields[0]
        self._set_param(key, val)

