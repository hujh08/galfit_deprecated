#!/usr/bin/env python3

'''
class to hold parameters to run galfit
'''

from .head import Head
from .model import Model
from .constraint import Constraints

from .fitlog import FitLogs
from .tools import gfname

from os.path import basename as os_basename
from .tools_path import abs_dirname, abs_join

class GalFit:
    valid_props={'comps', 'head',
                 'gfcons',
                 'logname', 'init_file', 'gfpath'}

    def __init__(self, filename=None, loadlog=False, loadcons=False):
        self.comps=[]  # collection of components
        self.head=Head()

        self.gfcons=Constraints(self.comps)   # constraints

        if filename!=None:
            if type(filename)==int:
                filename=gfname(filename)

            self.gfpath=abs_dirname(filename)
            self.logname=os_basename(filename) # name in fitlog

            self._load_file(filename)

        if loadlog:
            fitlog=self.get_abs_fname('fit.log')
            self._load_fitlog(fitlog)

        if loadcons:
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

        for mod, lmod in zip(self.comps, log.mods):
            mod.set_uncerts(lmod.uncerts)
            mod.set_flags(lmod.flags)

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

    def func_pix2world(self, method='all', **kwargs_wcs):
        '''
        method: 'all' or 'wcs'
            see astropy.wcs for details
        '''
        w=self.get_wcs(**kwargs_wcs)
        fwcs=getattr(w, method+'_pix2world')
        return lambda *args, origin=1, ra_dec_order=True:\
                    fwcs(*args, origin, ra_dec_order=ra_dec_order)

    def get_pixscale(self, **kwargs_wcs):
        '''
        return pixel scale of input fits
            in unit of arcsec/pixel
        '''
        from astropy.wcs.utils import proj_plane_pixel_scales
        import numpy as np
        w=self.get_wcs(**kwargs_wcs)
        pixel_scales=proj_plane_pixel_scales(w)*3600 # arcsec/pixel
        return np.average(pixel_scales)

    def func_pix2sec(self, **kwargs_wcs):
        pscale=self.get_pixscale(**kwargs_wcs)
        return lambda pix: pix*pscale

    def func_sec2pix(self, **kwargs_wcs):
        pscale=self.get_pixscale(**kwargs_wcs)
        return lambda sec: sec/pscale

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

    def get_xy_region(self, *args):
        return self.func_xy_region()(*args)

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

    # handle components
    ## add/remove component
    def add_comp(self, mod, vals=None, fixeds=None, Z=0, index=0):
        '''
        add component before index
        '''
        if isinstance(mod, Model):
            modnew=mod
        elif type(mod)==str or type(mod)==type:
            if type(mod)==str:
                mod=Model.get_model(mod)
            elif not issubclass(mod, Model):
                raise TypeError('unsupported model type: %s' % type(mod))
            modnew=mod(vals=vals, fixeds=fixeds, Z=Z)
        else:
            raise TypeError('unsupported model type: %s' % type(mod))

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

    def write(self, filename, overwrite=True):
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

    def chdir(self, dest, overwrite=True):
        fname=abs_join(dest, self.logname)
        self.write(fname, overwrite)

    # magic methods
    def __getattr__(self, prop):
        if prop in self.head.alias_keys:
            return getattr(self.head, prop)
        elif prop in {'chmod'}: # some head methods
            return getattr(self.head, prop)
        
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
        if type(prop)==int:
            return self.comps[prop]

        return self.__getattr__(prop)

    def __str__(self):
        return self._str()
