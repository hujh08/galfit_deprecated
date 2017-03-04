# package to handle galfit template file

## state

preliminary version.

It can just handle simple template file without truncation, Bn, C0 and Fn.

## description

In this package, templage is reprensted by a class GalFit, defined in galfit.py.
There are two parts in every valid template file ---- control parameters and models. Each of these is translated to a class, Head in head.py and Model in model.py respectively. And for every model, like sersic, expdisk, there is a corresponding subclass with capitalized name.
Every parameter in models is stored as class Parameter defined in parameter.py, which has properties val, fit and fix. This class is used to set the corresponding parameter free or not to fit.

## modules
### head
### model
### parameter
### galfit
### exception