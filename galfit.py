#!/usr/bin/env python3

'''
class to hold parameters to run galfit
'''
import os

from functools import partial

import numpy as np

from .head import Head
from .model import Model
from .constraint import Constraints

from .fitlog import FitLogs
from .tools import gfname
from .tools_gf import keys_patt, radec2skycoord,\
                      support_list_indices

import os.path as ospath
from .tools_path import abs_dirname, abs_join

class GalFit:
    log_props=['ndof', 'chisq', 'reduce_chisq'] # properties in figlog to store

    valid_props={'comps', 'head',
                 'gfcons',
                 'logname', '_log', *log_props,
                 'init_file', 'gfpath'}

    def __init__(self, filename=None, loadlog=False, loadcons=False, loadall=False):
        self.comps=[]  # collection of components
        self.head=Head()

        self.gfcons=Constraints(self.comps)   # constraints

        if filename!=None:
            if type(filename)==int:
                filename=gfname(filename)

            self.gfpath=abs_dirname(filename)
            self.logname=ospath.basename(filename) # name in fitlog

            self._load_file(filename)
        else:
            self.gfpath=os.getcwd()

        if loadall or loadlog:
            fitlog=self.get_abs_fname('fit.log')
            self._load_fitlog(fitlog)

        if (loadall or loadcons) and not self.is_none_cons():
            cons=self.get_abs_hdp('cons')
            self.gfcons._load_file(cons)

    # construct from file
    def _load_file(self, filename):
        blk=self.head   # current block
        with open(filename) as f:
            for line in f:
                if line.startswith('#  Input menu file: '):
                    self.init_file=line.split()[-1]
                    continue

                line=line.strip()
                if not line or line[0]=='#':
                    continue

                key, *vals=line.split()
                if key[-1]!=')':
                    continue

                key=key[:-1]
                if key=='0':
                    mdname=vals[0]
                    blk=Model.get_model(mdname)()
                    self.comps.append(blk)

                if key in blk.valid_keys:
                    blk._feed_key_fields(key, vals)

    def _load_fitlog(self, fitlog):
        logs=FitLogs(fitlog)
        if not hasattr(self, 'init_file'):
            log=logs.get_log(self.logname)
        else:
            log=logs.get_log(self.init_file, self.logname)

        self._log=log   # backup fitlog

        for mod, lmod in zip(self.comps, log.mods):
            mod.set_uncerts(lmod.uncerts)
            mod.set_flags(lmod.flags)

        # get information of fit
        for param in GalFit.log_props:
            setattr(self, param, getattr(log, param))

    # handle head
    ## absolute path for a file in head
    def get_abs_fname(self, fname):
        return abs_join(self.gfpath, fname)

    def get_abs_hdp(self, prop):
        return self.get_abs_fname(self.head.get_pval(prop))

    ## handle fits
    def get_fits_hdu(self, fitsname):
        from astropy.io import fits
        if fitsname[-1]==']':
            fitsname, hduid=fitsname[:-1].split('[')
            hduid=int(hduid)
        else:
            hduid=0

        return fits.open(fitsname)[hduid]

    ## handle input
    def get_input_hdu(self):
        fits_input=self.get_abs_hdp('input')
        return self.get_fits_hdu(fits_input)

    def get_input_head(self):
        return self.get_input_hdu().header

    def get_input_data(self):
        return self.get_input_hdu().data

    def get_input_data_region(self):
        xmin, xmax, ymin, ymax=self.head.get_pval('region')
        data=self.get_input_data()
        return data[(ymin-1):ymax, (xmin-1):xmax]

    def get_input_shape(self):
        return self.get_input_data().shape

    ### application of input head
    def get_exptime(self):
        '''
        get exptime of initial fits
            in unit of seconds
        '''
        fhead=self.get_input_head()
        if 'EXPTIME' not in fhead:
            return 1.
        return float(fhead['EXPTIME'])

    def func_mag2flux(self):
        '''
        return function to convert galfit mag to flux
        '''
        zerop=self.head.get_pval('zerop')
        exptime=self.get_exptime()
        return lambda mag: 10**(-(mag-zerop)/2.5)*exptime

    def get_mod_flux(self, modno):
        mod=self.comps[modno]
        if mod.is_sky():
            raise Exception('sky has no mag')
        mag=mod.get_pval('mag')
        return self.func_mag2flux()(mag)

    def get_flux_total(self):
        flux=0
        f=self.func_mag2flux()
        for mod in self.comps:
            if mod.is_sky():
                continue
            flux+=f(mod.get_pval('mag'))
        return flux

    def get_wcs(self, warnings_filter='ignore'):
        '''
        return wcs of input image
        '''
        import warnings
        from astropy.wcs import WCS as wcs
        fhead=self.get_input_head()
        with warnings.catch_warnings():
            warnings.simplefilter(warnings_filter)
            return wcs(fhead)

    def func_wcs(self, method, **kwargs_wcs):
        '''
        return methods, like pix2world, world2pix
            see astropy.wcs for details
        '''
        w=self.get_wcs(**kwargs_wcs)
        fwcs=getattr(w, method)
        def func(*args, origin=1, ra_dec_order=True):
            # support 1 layer array
            if len(args)==1:
                arg0=np.array(args[0])
                if len(arg0.shape)==1:
                    args=tuple(arg0)
            return fwcs(*args, origin, ra_dec_order=ra_dec_order)
        return func

    def func_pix2world(self, method='all', **kwargs_wcs):
        '''
        method: 'all' or 'wcs'
            see astropy.wcs for details
        '''
        method=method+'_pix2world'
        return self.func_wcs(method, **kwargs_wcs)

    def func_world2pix(self, method='all', **kwargs_wcs):
        '''
        method: 'all' or 'wcs'
        '''
        method=method+'_world2pix'
        return self.func_wcs(method, **kwargs_wcs)

    def get_radec_at(self, *args, **kwargs_mwcs):
        return self.func_pix2world(**kwargs_mwcs)(*args)

    def get_xy_at(self, *args, **kwargs_mwcs):
        return self.func_world2pix(**kwargs_mwcs)(*args)

    def get_mod_radec(self, modno, **kwargs_mwcs):
        mod=self.comps[modno]
        return self.get_radec_at(mod.get_xy(), **kwargs_mwcs)

    def get_mod_skycoord(self, modno, **kwargs_mwcs):
        '''
        return center with SkyCoord type
        '''
        radec=self.get_mod_radec(modno, **kwargs_mwcs)
        return radec2skycoord(radec)

    def _gen_func_to(self, modno, method, **kwargs_mwcs):
        '''
        return a function to calculate something in respect to ith model,
            like position angle, separation
        '''
        modskyc=self.get_mod_skycoord(modno, **kwargs_mwcs)
        def _func(method, *args, unit='deg'):
            skyc=radec2skycoord(*args)
            return getattr(getattr(modskyc, method)(skyc), unit)
        def func(*args, **kwargs):
            if type(args[-1])==str and 'unit' not in kwargs:
                kwargs['unit']=args[-1]
                args=args[:-1]
            return _func(*args, **kwargs)
        return partial(func, method)

    def func_pa_to(self, modno, **kwargs_mwcs):
        '''
        function to caculate position angle
        '''
        return self._gen_func_to(modno, 'position_angle', **kwargs_mwcs)

    def func_sep_to(self, modno, **kwargs_mwcs):
        '''
        function to caculate seperation
        '''
        return self._gen_func_to(modno, 'separation', **kwargs_mwcs)

    def get_sep_to(self, *radec, modno=0, **kwargs_mwcs):
        '''
        frequently used method to return separation to a position,
            choosing a representative model
            in unit of arcsec
        '''
        f=self.func_sep_to(modno, **kwargs_mwcs)
        return f(*radec, 'arcsec')

    def get_pixscale(self, **kwargs_wcs):
        '''
        return pixel scale of input fits
            in unit of arcsec/pixel
        '''
        from astropy.wcs.utils import proj_plane_pixel_scales
        w=self.get_wcs(**kwargs_wcs)
        pixel_scales=proj_plane_pixel_scales(w)*3600 # arcsec/pixel
        return np.average(pixel_scales)

    def func_pix2sec(self, **kwargs_wcs):
        pscale=self.get_pixscale(**kwargs_wcs)
        return lambda pix: pix*pscale

    def func_sec2pix(self, **kwargs_wcs):
        pscale=self.get_pixscale(**kwargs_wcs)
        return lambda sec: sec/pscale

    def get_sec_of(self, pix):
        return self.func_pix2sec()(pix)

    ## handle psf
    def get_psf_hdu(self):
        fits_input=self.get_abs_hdp('psf')
        return self.get_fits_hdu(fits_input)

    def get_psf_head(self):
        return self.get_psf_hdu().header

    def get_psf_data(self):
        return self.get_psf_hdu().data

    def get_psf_fwhm(self):
        fhead=self.get_psf_head()
        if 'FWHM' not in fhead:
            return None
        return float(fhead['FWHM'])

    ## handle region
    def get_region_shape(self):
        xmin, xmax, ymin, ymax=self.head.get_pval('region')
        return ymax-ymin+1, xmax-xmin+1

    def func_xy_region(self):
        '''
        return a function,
            which convert coordinates in original input to in region
        '''
        xmin, ymin=self.head.get_pval('region')[::2]

        return lambda x, y: (x-xmin, y-ymin)

    def func_world2region(self, **kwargs_wcs):
        world2pix=self.func_world2pix(**kwargs_wcs)
        pix2reg=self.func_xy_region()
        return lambda *args: pix2reg(*world2pix(*args))

    def get_xy_region_at_radec(self, *args):
        return self.func_world2region()(*args)

    def get_xy_region_at(self, *args):
        return self.func_xy_region()(*args)

    def get_mod_xy_region(self, modno=0):
        mod=self.comps[modno]
        return self.get_xy_region_at(*mod.get_xy())

    # use 1st comp as reprensative comp, and shorter name
    get_xy_region=get_mod_xy_region

    def confirm_region(self):
        '''
        confirm the region not exceeding the image
        '''
        fhead=self.get_input_head()
        nx=fhead['NAXIS1']
        ny=fhead['NAXIS2']
        region=self.head.get_param('region')
        if region[1]>nx:
            region[1]=nx
        if region[3]>ny:
            region[3]=ny
        if region[0]<1:
            region[0]=1
        if region[2]<1:
            region[2]=1

    ## handle constraints
    def bindcons(self, *args, name='constraints'):
        self.head.set_param('cons', name)
        self.add_cons(*args)

    def add_cons(self, *args):
        self.gfcons.add_cons(*args)

    def clear_cons(self):
        self.gfcons.clear()

    def is_none_cons(self):
        return self.head.get_pval('cons')=='none'

    def get_num_of_hard_free_params(self):
        '''
        number of free parameters limited by hard constraint
        '''
        return self.gfcons.get_num_of_hard_free_params()

    # handle components
    ## information of parameters
    def get_num_of_params(self):
        '''
        total number of parameters
        '''
        return sum([p.get_num_of_params() for p in self.comps])

    def get_num_of_fixed_params(self):
        '''
        total number of parameters
        '''
        return sum([p.get_num_of_fixed_params() for p in self.comps])

    def get_num_of_free_params(self):
        num_tot=self.get_num_of_params()
        num_fixed=self.get_num_of_fixed_params()
        num_hard=self.get_num_of_hard_free_params()

        return num_tot-num_fixed-num_hard

    ## add/remove component
    def add_comp(self, mod, vals=None, tofits=None, Z=0, index=None):
        '''
        add component before index
            if index is None, append it to comps
        '''
        if isinstance(mod, Model):
            modnew=mod
        elif type(mod)==str or type(mod)==type:
            if type(mod)==str:
                mod=Model.get_model(mod)
            elif not issubclass(mod, Model):
                raise TypeError('unsupported model type: %s' % type(mod))
            modnew=mod(vals=vals, tofits=tofits, Z=Z)
        else:
            raise TypeError('unsupported model type: %s' % type(mod))

        if index is None:
            self.comps.append(modnew)
        else:
            self.comps.insert(index, modnew)

    def del_comp(self, index=0):
        '''
        delete comp
        '''
        del self.comps[index]

    ### some specific models
    def add_sersic(self, *args, **keys):
        from .model import Sersic
        self.add_comp(Sersic, *args, **keys)

    def add_sky(self, *args, **keys):
        from .model import Sky
        self.add_comp(Sky, *args, **keys)

    ## free/freeze all parameters
    def set_all_comps_fit(self, tofit):
        '''
        set all components free to fit if `tofit` is True
        '''
        for c in self:
            c.set_all_params_fit(tofit)

    def free_all(self):
        self.set_all_comps_fit(True)

    def freeze_all(self):
        self.set_all_comps_fit(False)

    # output
    def _reset_comps_id(self, start=1):
        for i, comp in enumerate(self.comps, start):
            comp.set_id(i)

    def _str(self):
        lines=['='*80,
               '# IMAGE and GALFIT CONTROL PARAMETERS']
        lines.append(str(self.head))
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
        lines.append('# '+'-'*78)
        lines.append('#   par)    par value(s)    fit toggle(s)')
        lines.append('# '+'-'*78)
        lines.append('')

        self._reset_comps_id()
        for comp in self.comps:
            lines.append('# Component number: %i' % comp.id)
            lines.append(str(comp))
            lines.append('')

        lines.append('='*80)

        return '\n'.join(lines)

    def writeto(self, dest='.', overwrite=True):
        '''
        dest: file or directory
        '''
        if ospath.isdir(dest):
            return self.writeto_dir(dest, overwrite)
        else:
            return self.writeto_file(dest, overwrite)

    def writeto_file(self, filename, overwrite=True):
        '''write to a file'''
        if type(filename)==int:
            filename=gfname(filename)

        wrpath=abs_dirname(filename)
        if wrpath!=self.gfpath:
            self.head.chdir(self.gfpath, wrpath)

        with open(filename, 'w') as f:
            f.write(self._str()+'\n')

        if not self.gfcons.is_empty():
            self.gfcons.write(self.get_abs_hdp('cons'))

        # resume path of head
        if wrpath!=self.gfpath:
            self.head.chdir(wrpath, self.gfpath)

        return filename

    def writeto_dir(self, diranme, overwrite=True):
        '''write at a directory'''
        fname=abs_join(diranme, self.logname)
        self.writeto_file(fname, overwrite)
        return fname

    # magic methods
    def __iter__(self):
        '''
        Iteration's support for __getitem__
            can be seen as a "legacy feature"
        '''
        return iter(self.comps)

    def __getattr__(self, prop):
        if prop=='ncomp':
            return len(self.comps)

        Hkeys=self.head.alias_keys
        if prop in Hkeys:
            return getattr(self.head, prop)

        # some head methods
        Hmatch=keys_patt(Hkeys, ['ch', 'set_']).match(prop)
        if Hmatch:
            key=Hmatch.groupdict()['key']
            return partial(self.head._set_param, key)
        
        raise AttributeError(prop)

    def __setattr__(self, prop, val):
        if prop in GalFit.valid_props:
            # local property
            super().__setattr__(prop, val)
        elif prop in self.head.alias_keys:
            setattr(self.head, prop, val)
        else:
            raise AttributeError(prop)

    def __getitem__(self, prop):
        if support_list_indices(prop):
            return self.comps[prop]

        return self.__getattr__(prop)

    def __str__(self):
        return self._str()
