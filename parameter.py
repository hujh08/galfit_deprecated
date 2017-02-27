#!/usr/bin/env python3

'''
class for parameters
'''

class Parameter:
    '''
    stands for each parameters:
    property:
        val: value
        fit: free for fitting
        fix: fix for changing fit state
            Note: only fix property fit, but val is still changeable
    '''
    def __init__(self, val=0, fit=1, fix=0):
        self.val=val
        self.fit=fit
        self.fix=fix
        #self.state=[val, fit, fix]

    # magic method
    def __iadd__(self, num):
        self.val+=num
        return self
    def __isub__(self, num):
        self.val-=num
        return self
    def __imul__(self, num):
        #print('imul')
        self.val*=num
        return self
    def __itruediv__(self, num):
        #print('itruediv')
        self.val/=num
        return self

    # set state of parameter
    def setfit(self, fit=1):
        if not self.fix:
            self.fit=fit

    def setfix(self, fix=1):
        self.fix=fix

    ## frequently used functions
    def fit(self):
        self.setfit()
    def fix(self):
        self.setfix()

    def unfit(self):
        self.setfit(0)
    def unfix(self):
        self.setfix(0)

    # deep copy
    def copy(self):
        return Parameter(self.val, self.fit, self.fix)

    def copyto(self, param, force=False):
        if self is param:
            return

        param.val=self.val

        if not force and param.fix:
            return

        param.fit, param.fix = self.fit, self.fix

    def setfrom(self, param, force=False):
        #print('setfrom of parameter')
        if hasattr(param, '__float__'):
            self.val=float(param)
        elif not self is param:
            param.copyto(self, force)
