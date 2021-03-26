#!/usr/bin/env python3

'''
    base class of Header and Model

    that is a special dict-like collection, but with some differences
        -- only supporting keys in a given set
        -- user-friendly alias for some keys
        -- data type for a key is restricted
        -- value for some keys have default setup, and others must be given explicitly

    These (meta)classes are mainly for a unique way to handle data input and string print
'''

import re
import numbers

'''
    frequently used functions
'''
# inverse of alias dict: {key: [alias_names]}
def inverse_alias(alias):
    '''
        an alias is a dictionary with value as the alias names of the key,
            where value could be collection of different names

        return the inverse of this correspondence
    '''
    result={}
    for k in alias:
        for v in alias[k]:
            assert v not in result
            result[v]=k
    return result

# data type
def is_number_type(val):
    '''
        determine whether a data is number
    '''
    return isinstance(val, numbers.Number)

def is_float_type(val):
    '''
        determine whether a data is float
    '''
    return isinstance(val, numbers.Real) and not isinstance(val, numbers.Integral)

def is_int_type(val):
    '''
        determine whether a data is int
    '''
    return isinstance(val, numbers.Integral)

def is_str_type(val):
    '''
        determine whether a data is str
    '''
    return isinstance(val, str)

def is_vec_type(val):
    '''
        determine whether data could be treated as vector

        Current type as a vector
            list
            tuple
    '''
    return isinstance(val, list) or isinstance(val, tuple)

'''
    basic classes
'''

class MetaSlotsDict(type):
    '''
        meta class to create some attrs based on implement of class
    '''
    def __init__(self, *args, **kwargs):
        '''
            for a metaclass,
                `self` in `__init__` is actually the class to construct
            
            call `init_class` do some initiations to the clss
        '''
        self.init_class()

    # extract function for data type normalization
    def ext_func_type(self, val):
        '''
            extract a function `f` from the example `val`
                which is used to normalize other arguments by `f(arg)`
                    where the input arguments distinguish string and other type

            distinguish 2 types of data:
                vector: `val` is list or tuple, or other supported type
                    see function `is_vec_type` for detail
                scalar: other types

            The behavior depends on 3 functions
                is_vec_type:
                    determine whether a data is of vector type
                get_func_scalar:
                    return a function to handle scalar type
                        and combination of vector type
                combine_func_vector:
                    combine functions and
                        return a function to handle vector type
                str_split_to_vec:
                    function to split string to construct a vector data
                        two frequently-used way: `space_split_to_vec` and `comma_split_to_vec`
                        use `space_split_to_vec` by default
                    allowed to be implemented to accept kwargs
            These 3 functions could be reloaded
            BUT MUST AS A classmethod
        '''
        fv=self.get_func_scalar(val)
        if not self.is_vec_type(val):
            return fv

        # vector
        fes=[]  # function for elements
        for v in val:
            fes.append(self.ext_func_type(v))

        return self.combine_func_vector(fv, fes)

    def is_vec_type(self, val):
        '''
            determine wheter the example `val` is a vector

            the data type must support indexing

            Current type as a vector
                list
                tuple
        '''
        return is_vec_type(val)

    def get_func_scalar(self, val):
        '''
            return a function to handle scalar and combine elements in vector
        '''
        return val.__class__

    def combine_func_vector(self, f_vec, f_eles):
        '''
            combine functions to construct a function to handle vector data

            Parameter:
                func_eles:
                    function to handle elements in vector

                func_vec:
                    function to combine elements
        '''
        def func_vector(arg, **kwargs):
            '''
                function for a vector

                different treatment when `arg` is str

                `kwargs` are all passed to `str_split_to_vec` if any needed
            '''
            if isinstance(arg, str):
                return func_vector(self.str_split_to_vec(arg, **kwargs))

            assert len(arg)==len(f_eles)
            return f_vec([f(arg[i]) for i, f in enumerate(f_eles)])

        return func_vector

    def str_split_to_vec(self, s, comma_split=False):
        '''
            split string to construct a vector data
        '''
        if comma_split:
            f_split=self.comma_split_to_vec
        else:
            f_split=self.space_split_to_vec
        return f_split(s)

    ## some frequently used split way
    def space_split_to_vec(self, s):
        '''
            split string with whitespace
        '''
        return s.split()

    _ptn_split=re.compile(r'\s*,\s*')
    def comma_split_to_vec(self, s):
        '''
            split string with comma, or other ptn
        '''
        return self._ptn_split.split(s)

class SlotsDict(object, metaclass=MetaSlotsDict):
    '''
        a special dict-like collection structure
            where it is only allowed for specific keys and corresponding data type
                just like some fixed slots, waiting to fill in data

        required properties:
            keys_sorted: list of valid keys with a given order

            keys_alias: user-friendly alias
                with format, {key: [alias_names]}

            values_example: example of a value
                from this example, data type could be extracted

                for the example `val`, a function is extracted
                    which is used to normalize input when setattr

                different ways for 2 types of data:
                    scalar: just use `val.__class__`
                    vector: nested way
                    see function `ext_func_type` for detail

            values_alias: alias of values for some keys
                kind of similar as `keys_alias`, except for values
                first alias is also usd as key name if not given explicitly

            values_valid: valid values for some key
                only value in this set are allowed as input

            keys_name: user-friendly name of a key
                if not exists, use the prop-self

            keys_comment: comment
                `keys_name`, `keys_comment` are used for print

            keys_optional: optional keys
                if optional and not set explicitly, use the value in `values_default`

            values_default: default value for optional keys
                if values_example specified in a class,
                    it would then follow this `values_example` in `init_class`

        properties constructed in metaclass
            keys_valid: valid keys
                construct from `keys_sorted`

            map_keys_alias: map alias to key
                construct from `keys_alias`

            map_values_alias: map alias to a value
                construct from `values_valid`

            values_funcs_type: map key to a function to normalize data
                construct from `values_example`

        classes of header, model are implemented based on this.
    '''
    keys_sorted=[]
    keys_alias={}
    values_example={}
    values_alias={}
    values_valid={}

    keys_optional=set()
    values_default={}

    keys_name={}
    keys_comment={}

    # initiation of class
    @classmethod
    def init_class(cls):
        '''
            initiation of class
                would be called in the metaclass

            construct some attributions from other existed ones

            create attrs for specific implementation
            including:
                keys_valid: from keys_sorted
                map_keys_alias: from keys_alias
                values_funcs_type: from values_example
                map_values_alias: from values_alias

            addtional treatment to
                values_default: some values would be copied from `values_examples`
        '''
        # initiation required props
        props_req=['keys_sorted', 'keys_alias', 'values_example']

        # keys_valid
        if 'keys_sorted' in cls.__dict__:
            cls.keys_valid=set(cls.keys_sorted)

        # map_keys_alias
        if 'keys_alias' in cls.__dict__:
            cls.map_keys_alias=inverse_alias(cls.keys_alias)

            # update keys_name
            if 'keys_name' not in cls.__dict__:
                cls.keys_name={}

            for k in cls.keys_alias:
                if k not in cls.keys_name:
                    cls.keys_name[k]=cls.keys_alias[k][0]

        # values_funcs_type
        if 'values_example' in cls.__dict__:
            cls.values_funcs_type={k: cls.ext_func_type(v)
                                    for k, v in cls.values_example.items()}

        # map_values_alias
        if 'values_alias' in cls.__dict__:
            cls.map_values_alias={k: inverse_alias(s)
                                    for k, s in cls.values_alias.items()}

        # values_default: copy some values from values_example
        if 'values_example' in cls.__dict__:
            if 'values_default' not in cls.__dict__:
                # not inherit from parent class. use {} by default
                cls.values_default={}

            # copy all valid keys
            for k in cls.keys_sorted:
                if k not in cls.values_example:
                    continue

                if k not in cls.values_default:
                    cls.values_default[k]=cls.values_example[k]

    # initiation of instance
    def __init__(self):
        '''
            initiation of class

            create a dict named `pars` to storing all data
        '''
        self.__dict__['pars']={}

    # `in` method
    def __contains__(self, prop):
        '''
            when use 'prop in object', this method is called
        '''
        return self.get_std_key(prop) in self.keys_valid

    # functions to handle keys
    def get_std_key(self, prop):
        '''
            get a standard key for a given `prop`

            mainly translate the alias
        '''
        if prop in self.map_keys_alias:
            prop=self.map_keys_alias[prop]

        return prop

    def get_key_name(self, key):
        '''
            return a user-friendly name for a key
        '''
        if key in self.keys_name:
            return self.keys_name[key]

        return key

    ## type of key
    def is_valid_key(self, key):
        '''
            whether a valid key
        '''
        key=self.get_std_key(key)
        return key in self.keys_valid

    def is_opt_key(self, key):
        '''
            whether an optional key
            
            an optional key must be valid
        '''
        key=self.get_std_key(key)
        return self.is_valid_key(key) and key in self.keys_optional

    def is_set_key(self, key):
        '''
            whether a key is set explicitly
        '''
        key=self.get_std_key(key)
        return key in self.pars

    ### for unset optional keys
    def touch_opt_key(self, key):
        '''
            touch an optional key,
                if it is not in `self.pars`, put it
        '''
        if self.is_set_key(key) or not self.is_opt_key(key):
            # do nothing to set or non-optional keys
            return

        SlotsDict.set_prop(self, key, self.get_val(key))

    # useless, deprecate
    # ## optional/required keys
    # def keys_split_req_opt(self):
    #     '''
    #         split keys to required and optional keys
    #             with the order in `keys_sorted`

    #         return reqs, opts
    #     '''
    #     reqs=[]
    #     opts=[]

    #     for k in self.keys_sorted:
    #         if k in self.keys_optional:
    #             opts.append(k)
    #         else:
    #             reqs.append(k)

    #     return reqs, opts

    # fundamental methods to get/set attribution
    def get_val(self, prop):
        '''
            only accessible for valid keys
        '''
        prop=self.get_std_key(prop)
        if prop not in self.keys_valid:
            raise Exception('unsupported prop for get: '+self.get_key_name(prop))

        if prop not in self.pars:
            # if not set, use value in values_default
            if prop in self.keys_optional:
                if prop not in self.values_default:
                    raise Exception('no default value for optional prop: '
                                            +self.get_key_name(prop))
                return self.values_default[prop]

            raise Exception('unset parameter: '+self.get_key_name(prop))

        return self.pars[prop]

    def set_prop(self, prop, val):
        '''
            only setattr for valid keys
        '''
        prop=self.get_std_key(prop)
        if prop not in self.keys_valid:
            raise Exception('unsupported prop for set: '+self.get_key_name(prop))

        if prop in self.map_values_alias:
            map_vals=self.map_values_alias[prop]
            if val in map_vals:
                val=map_vals[val]

        if prop in self.values_funcs_type:
            # if not in `values_funcs_type`, no any treatment
            val=self.values_funcs_type[prop](val)

        if prop in self.values_valid:
            values_valid=self.values_valid[prop]
            if val not in values_valid:
                name=self.keys_name.get(prop, prop)
                raise Exception('unexpected value for par \'%s\'. Only accept %s'
                                    % (name, str(values_valid)))
        self.pars[prop]=val

    ## magic methods
    ### getattr/setattr
    def __getattr__(self, prop):
        '''
            work like 'object.prop'
        '''
        return self.get_val(prop)

    def __setattr__(self, prop, val):
        '''
            work like 'object.prop=val'
        '''
        self.set_prop(prop, val)

    ### setitem/setitem
    def __getitem__(self, prop):
        '''
            work like 'object[prop]'
        '''
        return self.get_val(prop)

    def __setitem__(self, prop, val):
        '''
            work like 'object[prop]=val'
        '''
        self.set_prop(prop, val)

    # convert to string
    def strprint_of_key(self, key):
        '''
            string used for print for a key
        '''
        return str(self.get_std_key(key))

    def strprint_of_val(self, val):
        '''
            string used for print for val

            return str or None
                if None, hint that it may be omitted
        '''
        if not self.__class__.is_vec_type(val):
            return self.strprint_of_val_scalar(val)
        else:
            return self.strprint_join_vec([self.strprint_of_val(s) for s in val])

    def strprint_of_val_key(self, key):
        '''
            string used for print for val corresponding to val

            return str or None
                if None, hint that it may be omitted
        '''
        val=self.get_val(key)
        return self.strprint_of_val(val)

    def strprint_of_val_scalar(self, val):
        '''
            string used for scalar val
        '''
        return str(val)

    def strprint_join_vec(self, list_str):
        '''
            combine list of string
        '''
        return ' '.join(list_str)

    def linefields_for_print(self, key):
        '''
            return a list of 2 or 3 string, [key, val, (comments)]
                which is used to contruct a line for a key
        '''
        sval=self.strprint_of_val_key(key)
        if sval is None:
            return []

        skey=self.strprint_of_key(key)  # convert to standard key
        
        fields=[skey, sval]

        # comments
        if key in self.keys_comment:
            fields.append(self.keys_comment[key])
        return fields

    _line_fmt2='%s %s'        # formt for 2 fields
    _line_fmt3='%s %s # %s'   # formt for 3 fields
    def line_for_print(self, key):
        '''
            return a string for a key used to print as a line
                or None, to hint to omit this key
        '''
        fields=tuple(self.linefields_for_print(key))
        if len(fields)<1:
            return None

        if len(fields)<=2:
            fmt=self._line_fmt2
        else:
            fmt=self._line_fmt3

        return fmt % fields

    def iter_lines(self):
        '''
            iteration to return lines of keys
        '''
        for key in self.keys_sorted:
            s=self.line_for_print(key)
            if s is not None:
                yield s

    def str_print(self):
        '''
            string output to print
        '''
        lines=list(self.iter_lines())
        return '\n'.join(lines)

    ## __str__
    def __str__(self):
        '''
            user-friendly
        '''
        return self.str_print()

    # def __repr__(self):
    #     '''
    #         developer-friendly
    #     '''
    #     pass

# class designed for galfit
class GFSlotsDict(SlotsDict):
    '''
        class designed for galfit input file

        reload some functions
    '''
    # reload of some functions
    ## data type to input
    @classmethod
    def get_func_scalar(cls, val):
        '''
            return a function to handle scalar and combine elements in vector

            special treatment to str, int
        '''
        if is_str_type(val):
            return cls.func_str

        if is_int_type(val):
            return cls.func_int

        return SlotsDict.get_func_scalar(val)

    ### functions for str, int
    @classmethod
    def func_str(cls, val):
        '''
            function for str

            only allow str type
        '''
        assert is_str_type(val)
        return str(val)

    @classmethod
    def func_int(cls, val):
        '''
            function for str

            only allow int, str
        '''
        assert is_str_type(val) or is_int_type(val)
        return int(val)

    ## stringlizing
    _fmt_float='%.3f'
    def strprint_of_val_scalar(self, val):
        '''
            reload string-lizing of scalar

            just do special treatment to float number

            a class property is used here: `_fmt_float`
                it could be reloaded for different action
        '''
        if is_float_type(val):
            if abs(val)<1e-3:
                return '%g' % val
            return self._fmt_float % val

        return super().strprint_of_val_scalar(val)

    ### 2 formats
    _line_fmt2='%s) %s'           # formt for 2 fields
    _line_fmt3='%s) %-19s # %s'   # formt for 3 fields
