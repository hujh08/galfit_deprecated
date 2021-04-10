#!/usr/bin/env python3

'''
    functions to handle FITS image file
'''

import re

import numpy as np
from astropy.io import fits

'''
    extended file name syntax
        see readme.md for detail
'''

from collection import is_int_type

# re pattern
fmt_sqbra=r'\[\s*({0})\s*\]'  # enclosed in square brackets

## section
ptn_int=re.compile(r'[-+]?\d+')
ptn_slice=re.compile(r'(?:(-?\*)|({0}):({0}))(?::({0}))?'.format(ptn_int.pattern))
ptn_sect=re.compile(r'{0}(?:\s*,\s*{0})*'.format(ptn_slice.pattern))
ptn_syn_sect=re.compile(fmt_sqbra.format(ptn_sect.pattern))  # with square bracket

## HDU
ptn_xten=re.compile(r'IMAGE|ASCII|TABLE|BINTABLE|I|A|T|B')
ptn_extname=re.compile(r'([^,]+)(?:{0}(\d+))?(?:{0}({1}))?'.format(r'\s*,\s*', ptn_xten.pattern))
ptn_hdu=re.compile(r'({0})|({1})'.format(ptn_int.pattern, ptn_extname.pattern),
                    flags=re.IGNORECASE)
ptn_syn_hdu=re.compile(fmt_sqbra.format(ptn_hdu.pattern), flags=re.IGNORECASE)

## extended file name
ptn_extfname=re.compile(r'(?P<fname>.*?)(?P<hdu>{0})?\s*'
                        r'(?P<sect>{1})?\s*'.format(ptn_syn_hdu.pattern,
                                                     ptn_syn_sect.pattern),
                            flags=re.IGNORECASE)

# parser of extended file name
def parse_ext_fitsname(fitsname):
    '''
        parse an extended file name

        return fitsname, hdu ext, image section
            if any not specified, use None
    '''
    # '.*' exists in ptn_extfname, it would match every string
    dict_fhs=ptn_extfname.fullmatch(fitsname).groupdict()

    fname=dict_fhs['fname']
    hdu=dict_fhs['hdu']
    sect=dict_fhs['sect']

    # hdu
    if hdu is not None:
        hdu=ext_dict_hdu(hdu)

    # image section
    if sect is not None:
        sect=ext_slices_sect(sect)

    # return
    return fname, hdu, sect

## ext dict of hdu
def ext_dict_hdu(s):
    '''
        extract a information for hdu

        two types to return:
            extno
            extname, extver, xtension
                where extver, xtension could be None if not existed
    '''
    m=ptn_syn_hdu.fullmatch(s)
    if not m:
        return None

    fields=m.groups()

    # extno
    if fields[1] is not None:
        return int(fields[1])

    # extname
    extname, extver, xtension=fields[-3:]
    assert extname is not None

    d=dict(extname=extname)
    
    ## extver
    if extver is not None:
        extver=int(extver)

    ## xtension
    if xtension is not None:
        xtension=normal_xtension(xtension)

    return extname, extver, xtension

### normalize xtension
def normal_xtension(x):
    '''
        normalize xtension

        upper case
        IMAGE, ASCII, TABLE, BINTABLE
    '''
    x=x.upper()

    if len(x)==1:
        map_abbr=dict(I='IMAGE', T='TABLE', A='ASCII', B='BINTABLE')
        x=map_abbr[x]
    else:
        assert x in {'IMAGE', 'TABLE', 'ASCII', 'BINTABLE'}

    return x


## ext slices for image section
def ext_slices_sect(s):
    '''
        extract slices for image section
    '''
    m=ptn_syn_sect.fullmatch(s)
    if not m:
        return None

    items=ptn_slice.findall(s)

    return [ext_slice_sectitem(*t) for t in items]

def ext_slice_sectitem(*args):
    '''
        extract slice from an item of section

        2 types of arguments:
            1 arg: string of slice
            4 args: groups from `ptn_slice`
    '''
    if len(args)==1:
        print(args)
        m=ptn_slice.fullmatch(args[0])
        assert m
        args=m.groups()
    elif len(args)!=4:
        raise Exception('only support 1 or 4 args, but got %i' % len(args))

    # groups from `ptn_slice`
    asterisk, start, end, step=args

    # step
    if not step:
        step=1
    else:
        step=int(step)

    # asterisk
    if asterisk:
        if asterisk[0]=='-':
            step*=-1
        return None, None, step

    # start, end
    start=int(start)
    end=int(end)

    return start, end, step

'''
    functions to locate HDU and image section
'''

# bottom function to locate HDU
def locate_hdu(hdulist, ext=None):
    '''
        locate a hdu in given hdulist

        Parameter:
            ext: None, int, or tuple
                if None, return first HDU
                if int, it is index of target HDU in list
                if tuple, two types:
                    1 element : same as int
                    3 elements: extname, extver, xtension
                        last two terms are optional,
                            None for missing

                        extname:  value of EXTNAME or HDUNAME keyword
                        extver:   value of EXTVER keyword
                        xtension: value of XTENSION keyword
    '''
    if ext is None:
        return hdulist[0]

    # extno
    if is_int_type(ext):
        return hdulist[ext]

    if len(ext)==1:
        k=ext[0]
        assert is_int_type(k)
        return hdulist[k]
    elif len(ext)!=3:
        raise Exception('only support 1 or 4 elements in ext. '
                        'but got %i' % len(ext))

    # extname, extver, xtension
    extname, extver, xtension=ext
    assert extname is not None

    for hdu in hdulist:
        hdr=hdu.header

        # extname
        if 'EXTNAME' in hdr:
            if hdr['EXTNAME']!=extname:
                continue
        elif 'HDUNAME' in hdr:
            if hdr['HDUNAME']!=extname:
                continue
        else:
            continue

        # extver
        if extver is not None:
            if 'EXTVER' not in hdr:
                continue

            if hdr['EXTVER']!=extver:
                continue

        # xtension
        if xtension is not None:
            if 'XTENSION' not in hdr:
                continue

            xtension=normal_xtension(xtension)
            x0=normal_xtension(hdr['XTENSION'])
            if x0!=xtension:
                continue

        # find matched HDU
        return hdu

    # no HDU found
    s='EXTNAME='+extname  # error message
    if extver is not None:
        s+=', EXTVER=%i' % extver
    if xtension is not None:
        s+=', XTENSION=%s' % xtension

    raise Exception('no HDU found for [%s]' % s)

# bottom function for image section
def image_section(hdu, sect=None):
    '''
        do image section to a HDU
            section is also done to WCS if existed

        Parameter:
            sect: None, or list of tuple (start, end, stop)
                if None, return a copy

                order of tuple in sect is same as 'NAXIS' in header

                sect would be normalize by `normal_sectlist`
                    if length of list is not equal to NAXIS
                        missing tuples are raised by (None, None, 1)

    '''
    assert hdu.is_image   # only do to image hdu

    hdu=hdu.copy()   # not change inplace

    if sect is None:
        return hdu

    # crop header at first
    #     if assign data to hdu.data, header also changes
    hdu.header=imgsect_crop_header(hdu.header, sect)

    # crop data
    hdu.data=imgsect_crop_data(hdu.data, sect)

    return hdu

## normalize image section tuple according to length in an axis
def normal_sectlist(sectlist, naxis):
    '''
        normal list of sect tuple acoording to naxis

        `naxis`: number of pixels in all axes
            order of tuple in list is same as 'NAXIS' in header

            if length of list is not equal to NAXIS
                missing tuples are raised by (None, None, 1)

    '''
    nax=len(naxis)

    # complete :param `sectlist` to the same as dims
    assert len(sectlist)<=nax
    if len(sectlist)<nax:
        sectlist.extend([(None, None, 1)*(nax-len(sectlist))])

    # normal sect tuple (start, end, step)
    return [normal_sect_item(s, nx) for s, nx in zip(sectlist, naxis)]

def normal_sect_item(item, nx):
    '''
        normalize a section tuple `(start, end, step)`
            according to axis length, `nx`

        support None or negative for start and end
            if negtive, meaning pixel couting from tail

            if None, meaning start or end in head or tail
                according to sign of step

        Result:
            start, end, step: all integral
                start, end: index starting from head
                    but 1 for head
                    might be 0 or negtive, meaning left of head

        Parameter:
            item: int, or tuple (start, end, step) or (start, end) or (end,)
                for int:
                    it means first or last some pixels
                        if positive or negative

                for tuple:
                    start, end, step: None, or non-zero integral

                    None for missing element

                    if step is None, use 1

            nx: number of pixel in the axis
    '''
    if is_int_type(item):
        end=item
        start=None

        step=1
        if end<0:
            step=-1
        elif end==0:   # no pixel included
            start=1
            end=0
    else:
        if len(item)==1:
            item=(None, *item, None)
        elif len(item)==2:
            item=(*item, None)
        elif len(item)!=3:
            raise Exception('only support int or tuples with 1,2,3 args')

        start, end, step=item

    # step
    if step is None:
        step=1
    assert step!=0

    # start, end
    start=norm_ind_pix(start, -step, nx)
    end=norm_ind_pix(end, step, nx)

    return start, end, step

def norm_ind_pix(ind, d, nx):
    '''
        normal index of pixel

        support nx=0 and ind=negative, None

        `nx`: number of pixel in the axis

        `ind` could be None, non-zero integral
            if None, sign of d (kind of direction) means to use head or tail 
                d<0 for head, and d>0 for end (only non-zero)

            if positive, 1 for the first pixel
            if negative, means index counting from end (-1 for the last)

        return index of pixel starting from head
            but 1 for head
                0 or negative for left of head
    '''
    assert nx>=0
    assert d!=0

    if ind is None:
        if d<0:
            return 1
        else:
            return nx

    # if not None, cannot be 0
    if ind<0:
        ind+=nx+1

    return ind

## function to image data
def imgsect_crop_data(data, sect=None):
    '''
        crop image data for given section `sect`

        Parameter:
            sect: list of tuple (start, end, step)
                `start` and `end` start from 1, not 0 as ndarray index

                order of tuple in list are x, y, ...
                    reversed with ndarray index
    '''
    if sect is None:
        return np.copy(data)

    naxis=list(reversed(data.shape))  # order of axis in fits header

    # normalize sect
    slices=[]
    for (x0, x1, d), nx in zip(normal_sectlist(sect, naxis), naxis):
        # assert nx>=0
        # assert d!=0

        if nx==0 or (x1-x0)*d<0:  # support empty axis
            slices.append(slice(2, 1))
            continue

        assert 1<=x0<=nx and 1<=x1<=nx

        # shift from pixel index to ndarray index
        x0-=1
        x1-=1

        # include end
        x1+=np.sign(d)
        if x1<0:
            x1=None

        slices.append(slice(x0, x1, d))

    return data[tuple(reversed(slices))]

## function to image header
def imgsect_crop_header(header, sect=None):
    '''
        crop FITS header for image section

        mainly handle WCS if existed

        work depends on keywords:
            CRPIX1, CRPIX2, ...
            CD1_1, CD1_2, CD2_1, CD2_2, ...
    '''
    header=header.copy() # not change in place

    if sect is None or 'CRPIX1' not in header:
        return header

    nax=header['NAXIS']
    naxis=[header['NAXIS%i' % i] for i in range(1, nax+1)]

    for i, (x0, _, d) in enumerate(normal_sectlist(sect, naxis)):
        assert d!=0

        # CRPIX
        key='CRPIX%i' % (i+1)
        header[key]=(header[key]-x0)/d+1  # +1 for 1-based pix index

        # CDj_i
        if d==1:
            continue

        for j in range(nax):
            key='CD%i_%i' % (j+1, i+1)
            header[key]*=d

    return header

'''
    imcopy, working similarly as IRAF.imcopy
        support extended file name and image section
'''
def imcopy(fitsname, output=None, extended_file_name=True, **kwargs):
    '''
        imcopy

        support extended file name and image section

        `output`: fitsname of output
            if None, return result hdu

            support '!' in begining of file name to overwrite

        explicit ext, sect and overwrite is supported
            by optional keyword arguments
        But specify in one place, fitsname or kwargs
            conflict raised if repeated

        `extended_file_name`: bool
            whether to support extended file name
    '''
    # parse extended fitsname
    if extended_file_name:
        fitsname, ext, sect=parse_ext_fitsname(fitsname)
    else:
        ext=sect=None

    ## check conflict
    if ext is not None:
        assert 'ext' not in kwargs
    elif 'ext' in kwargs:
        ext=kwargs.pop('ext')

    if sect is not None:
        assert 'sect' not in kwargs
    elif 'sect' in kwargs:
        sect=kwargs.pop('sect')

    # '!' in output fitsname
    if output is not None and extended_file_name:
        if output[0]=='!':
            # avoid conflict
            assert 'overwrite' not in kwargs

            output=output[1:]
            kwargs['overwrite']=True

    # hdulist
    hdulist=fits.open(fitsname)

    # locate HDU
    hdu=locate_hdu(hdulist, ext)

    # image copy
    if sect is not None:
        hdu=image_section(hdu, sect)

    # write or return
    if output is None:
        return hdu

    hdu.writeto(output, **kwargs)
