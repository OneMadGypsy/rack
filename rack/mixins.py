from   __future__  import annotations
from   dataclasses import asdict, dataclass, field, fields, InitVar, KW_ONLY
from   typing      import Any, Iterable, Iterator
import json


# __all__ would literally be all
# importing this class is intended to conveniently import everything...
# including the above imports


""" Dataclass_mi: dataclass mixin for useful dictionary-related behavior
  supports:
    *) .keys(), .values(), .items()
    *) dictionary unpacking
    *) pretty-print self as json
    *) return self as dict
    *) return kwargs from requested keys to include or omit
    *) return args from requested keys to include or omit
    *) reassign any/all fields in one call
      +) optional __post_init__ call after reassignment
"""
class Dataclass_mi:
    @property
    def asdict(self) -> dict:
        return asdict(self)
      
    def items(self) -> Iterable:
        return self.asdict.items()
      
    def values(self) -> Iterable:
        return self.asdict.values()
        
    # required for dictionary unpacking
    def keys(self) -> Iterable:
        return self.asdict.keys()
        
    # create kwargs from args of keys to include or omit
    def kwargs(self, *args, omit:bool=False) -> dict:
        return {key:getattr(self, key) for fld in fields(self) if ((key := fld.name) in args) ^ omit}
    
    # create kwargs from args of keys to include or omit
    def args(self, *args, omit:bool=False) -> list:
        return [getattr(self, key) for fld in fields(self) if ((key := fld.name) in args) ^ omit]
        
    # required for dictionary unpacking  
    # an error will be raised if this key does not exist
    def __getitem__(self, key:str) -> Any:
        return getattr(self, key)
    
    # json no indent
    def __repr__(self) -> str:
        return json.dumps(self.asdict, default=str)
    
    # pretty-printed json
    def __str__(self) -> str:
        return json.dumps(self.asdict, indent=4, default=str)
    
    # reassign fields from kwargs and optionally call __post_init__
    def __call__(self, initvars:dict|None=None, **kwargs) -> Dataclass_mi:
        # if key exists, set value. otherwise, ignore.
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
          
        # if you want __post_init__ to be called, but it doesn't accept arguments -
        # pass initvars as an empty dict
        if initvars is not None: 
            self.__post_init__(**initvars)
          
        # let this be an inline method        
        return self
        

 