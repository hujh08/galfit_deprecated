#!/usr/bin/env python3

'''
    class for a fitting parameter
        with property val, state, uncertainty (optional)
'''

from collection import is_str_type, is_int_type, is_number_type

class Parameter:
    '''
        class of fitting parameter

        3 main property: val, state, uncertainty
            val: value of the parameter
            state: fitting state
                whether the parameter is free (1) or freeze (0) to fit
            uncert: uncertainty of fitting result
                optional
    '''
    def __init__(self, *args):
        '''
            initiation of parameter

            only allow 1,2,3 arguments
                1-arg: str, vector, or number
                    if str, split and analysis agian
                2-args: val, state
                    val: str, or numbers
                    state: str, or int
                3-args: val, state, uncertainty
                    uncertainty: optional, None, str, or numbers
        '''
        if len(args)==1:
            v=args[0]
            if is_str_type(v):
                return self.__init__(*v.split())

            if not is_number_type(v):
                return self.__init__(*v)

            self.__init__(v, 0)

        elif len(args)>3:
            raise Exception('only allow 1-3 arguments, got %i' % (len(args)))
        else:
            self.set_val(args[0])
            self.set_state(args[1])

            if len(args)>2:
                self.set_uncert(args[2])

    # methods to set properties: val, state, uncert
    def set_val(self, v):
        '''
            set property `val`
        '''
        self.val=float(v)

    def set_state(self, v):
        '''
            set property `val`

            only allow int, str
        '''
        assert is_int_type(v) or is_str_type(v)
        self.state=int(v)

    def set_uncert(self, v):
        '''
            set property `uncert`
        '''
        self.uncert=float(v)

    ## intercept other setting
    def __setattr__(self, prop, val):
        props_valid={'val', 'state', 'uncert'}
        if prop not in props_valid:
            raise Exception('only allow properties: %s' % str(props_valid))

        super().__setattr__(prop, val)


    # stringlizing
    def str_val(self):
        '''
            str of val
        '''
        if abs(self.val)<1e-3:
            return '%.3e' % self.val
        else:
            return '%.4f' % self.val

    def __str__(self):
        '''
            user-friendly stringlizing
        '''
        s=self.str_val()
        return '%-11s %i' % (s, self.state)

    def __repr__(self):
        '''
            developer-friendly
        '''
        ss='%g, %i' % (self.val, self.state)
        if hasattr(self, 'uncert'):
            ss+=', %g' % self.uncert

        name=self.__class__.__name__
        return '%s(%s)' % (name, ss)
