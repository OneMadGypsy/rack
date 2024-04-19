import re
from typing import Any, Callable

__all__ = ('Query',)

_noop = lambda _: _

# formats the RSE of an `in` conditon with `op`
# if `op` is `_noop`, this does nothing 
def _format_in(data:Any, op:Callable=_noop) -> Any:
    if op is _noop: return data
    
    if isinstance(data, list|tuple|set):
        results = type(data)(op(f'{x}') for x in data)
    else:
        results = op(f'{data}')
        
    return results

# all of these functions support str.lower
_in  = lambda a, b, op=_noop: op(a) in _format_in(b, op)
_sw  = lambda a, b, op=_noop: op(a).startswith(op(b))
_ew  = lambda a, b, op=_noop: op(a).endswith(op(b))
_eq  = lambda a, b, op=_noop: op(a) == op(b)

# dictionary of possible operators for query comparisons
# !  : not (must be first character of operator - exs: !=(not equal), !->(not in))
#      * cannot be used with any less-than, greater-than or `is` comparisons
# .  : apply str.lower() to `a` and `b` before comparing (must be last character of operator - ex: <%.)
#      * cannot be used with any less-than, greater-than or `is` comparisons
# <% : a.startswith(b)
# %> : a.endswith(b)
# -> : a in b
# => : a is b
_operators = {'!->.' :lambda a,b: not _in(f'{a}', b, str.lower),
              '!<%.' :lambda a,b: not _sw(f'{a}', b, str.lower),
              '!%>.' :lambda a,b: not _ew(f'{a}', b, str.lower),
              '!=.'  :lambda a,b: not _eq(f'{a}', b, str.lower),
              '->.'  :lambda a,b: _in(f'{a}', b, str.lower),
              '<%.'  :lambda a,b: _sw(f'{a}', b, str.lower),
              '%>.'  :lambda a,b: _ew(f'{a}', b, str.lower),
              '==.'  :lambda a,b: _eq(f'{a}', b, str.lower),
              '!->'  :lambda a,b: not _in(a, b),
              '!<%'  :lambda a,b: not _sw(a, b),
              '!%>'  :lambda a,b: not _ew(a, b),
              '!='   :lambda a,b: not _eq(a, b),
              '->'   :lambda a,b: _in(a, b),
              '<%'   :lambda a,b: _sw(a, b),
              '%>'   :lambda a,b: _ew(a, b),
              '=='   :lambda a,b: _eq(a, b),
              '=>'   :lambda a,b: a is b,
              '<='   :lambda a,b: a <= b,
              '>='   :lambda a,b: a >= b,
              '<'    :lambda a,b: a < b,
              '>'    :lambda a,b: a > b}
        
# format _operators keys for regex group
_oper = '|'.join(map(re.escape, _operators.keys()))
        
class Query:
    QUERY_DIVIDER = '::'
    LIST_DIVIDER  = ','
    ARGS_DIVIDER  = ';'
    
    OPERATOR_SPLIT = re.compile(fr'\s*({_oper})\s*').split
    NUMBER_MATCH   = re.compile(r'-?\d*(\.\d+)?').fullmatch
    STRING_MATCH   = re.compile(r'("|\')(?P<str>.*)\1').fullmatch

    @staticmethod
    def cast(value:str) -> list|float|int|bool|str|None:
        out   = None
        value = value.strip()
        
        if len((out := value.split(Query.LIST_DIVIDER))) > 1:
            out = [Query.cast(v) for v in out]
        elif (v := value.lower()) in ('true', 'false'):
            out = v == "true"
        elif m := Query.STRING_MATCH(value):
            out = m.group('str')
        elif m := Query.NUMBER_MATCH(value):
            out = (int,float)['.' in v](v)
            
        return out
    
    @staticmethod # reformat raw data to applicable query args
    def format(data:Any, _lvl:int=0) -> list:
        if isinstance(data, list|tuple|set):
            data = [Query.format(item, _lvl+1) for item in data]
            if _lvl: data = Query.LIST_DIVIDER.join(data)
        else:       
            data = f'"{data}"' if isinstance(data, str) else f'{data}'
            if not _lvl: data = [data]
        
        return data
    
    @staticmethod # check conditions against a data source
    def check_conditions(data:dict, conditions:str) -> bool:
        # stores condition results
        facts = []
    
        for cond in conditions.split(Query.ARGS_DIVIDER):
            # stores values and operators
            v, o = [], []
            
            # parse values and operators
            for c in Query.OPERATOR_SPLIT(cond):
                if (c := c.strip()) in _operators:
                    # store operator function
                    o.append(_operators.get(c))
                else:
                    # try data[c] else cast c
                    v.append(data.get(c, Query.cast(c)))
                
            # make sure values length is one more than operators              
            if (len(v) - len(o)) != 1:
                raise ValueError
                
            
            facts += [o[i](*v[i:i+2]) for i in range(len(o))]
        
        return all(facts)
    
    @staticmethod
    def params(query:str) -> list|None:
        params = [None, *query.split(Query.QUERY_DIVIDER)][-2:]
        return None if (None in params) else params
        
    @staticmethod
    def statement(typekey:str, conditions:str, *args, **kwargs) -> str:
        L      = len(args)
        nargs  = Query.format((*args, *(kwargs.values())))
        args   = nargs[:L]
        kwargs = dict(zip(kwargs.keys(), nargs[L:]))
        return Query.QUERY_DIVIDER.join((typekey, conditions.format(*args, **kwargs)))
    
