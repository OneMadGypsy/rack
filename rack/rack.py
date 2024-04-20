#from __future__ import annotations
import shelve, zipfile as zf
from   copy        import deepcopy
from   .query      import Query
from   .constants  import *
from   .mixins     import *


__all__ = 'Database', 'Entry', 'Tag', 'Query', 'UNIQUE'

    
@dataclass
class Entry(Dataclass_mi):
    # this version of type exists for registration and needs to be overwritten in a subclass
    TYPE = 'all'

    id  : str|int
    _   : KW_ONLY
    # this version of type exists for keying it's registered class when this entry is retrieved from the database
    # you should never manually set this, it is automatically set to self.TYPE 
    type: str = ''
    
    @staticmethod
    def unique_format(enttype:str, uid:int) -> str:
        return f'{enttype}{UNIQUE_SEP}{uid}'
    
    @property
    def unique(self) -> str:
        return Entry.unique_format(self.TYPE, self.id)
        
    @property
    def foreign_keys(self) -> tuple:
        return self.__fk
        
    @property 
    def asdict(self) -> dict:
        return {key:self.__serialize(value) for key, value in asdict(self).items()}
        
    @property
    def query(self) -> str:
        return f'{self.TYPE}{QUERY_SEP}'
        
    def __post_init__(self): 
        self.type    = self.TYPE        
        foreign_keys = []
        
        for fld in fields(self):
            """
            for every `.fk_somename` field create an `.somename` attribute
            `.somename` will be overwritten with the processed contents of `.fk_somename`
            however, in this step `.somename` is only created
            `.fk_somename` can be:
                # assuming `unique = EntrySubclass(0, **kwargs).unique`
                * key  : self.fk_somename = unique
                * keys : self.fk_somename = unique1, unique2, unique3
                * query: self.fk_somename = 'entrytype: title <%. "a"'
            """
            if m := FOREIGNKEY(fld.name):
                 key = m.group('key')
                 
                 if getattr(self, fld.name, None) or (not getattr(self, key, None)):
                     setattr(self, key, None)
                     
                 foreign_keys.append(key)
        
        self.__fk = tuple(foreign_keys)  
                 
    def __str__(self) -> str:
        obj = dict()
        
        for f in fields(self):
            key = f.name
            if m := FOREIGNKEY(key):
                 key = m.group('key')

            # use the fk results instead of the fk key(s)
            obj[key] = self.__serialize(getattr(self, key, None))
                
        return json.dumps(obj, indent=4)
        
    # convert all Entry|Iterable[Entry] to dict|Iterable[dict]
    # else value unchanged
    def __serialize(self, value:Any) -> Any:
        if isinstance(value, list|tuple|set):
            value = type(value)(map(self.__serialize, value))
        elif isinstance(value, Entry):
            value = value.asdict
        return value
  

# when retrieving a Tag from the database, you get back the value of `data`
# if `fk_data` is a query or foreign key(s), `data` will be overwritten with a processed `fk_data` value
@dataclass(slots=True)
class Tag(Entry):
    TYPE = "tag"
    data:Any    = None # any JSON serializable data or None
    fk_data:Any = None # setting this will overwrite `data`
    
            
class Database:
    TYPES   = (Entry,) # overwrite in a subclass
    ZIP_EXT = 'jiz'   # JSON in .zip (technically .7z)

    @property
    def _bin(self) -> dict:
        return self.__session_bin
    
    def __init__(self, dbname='generic', wipe:bool=False):
        self._db           = os.path.abspath(os.path.join(DAT, dbname))
        self.__registered  = dict()
        self.__session_bin = dict()
        
        # if the database doesn't exist - try to restore, else create
        if not (wipe or os.path.isfile(f'{self._db}.dat')):
            try   : self.restore()
            except: self.wipe()
        elif wipe: self.wipe()
            
        for T in (*self.TYPES, Tag):
            self.__register_type(T)        
        
    # entire database as "pretty-printed" json string
    def __str__(self) -> str:
        result = '{}'
        with shelve.open(self._db) as db:
            result = json.dumps(dict(db), indent=4, default=str)
        return result
        
    # entire database as json string
    def __repr__(self) -> str:
        result = '{}'
        with shelve.open(self._db) as db:
            result = json.dumps(dict(db), default=str)
        return result
       
    # get database entry by key or query     
    def __getitem__(self, query:str) -> Any:
        for entry in self.query_all(query, cast=False): 
            break
        else:
            with shelve.open(self._db) as db:
                entry = db.get(query, {})
                
        if not (enttype := entry.get('type')):
            raise ValueError('entry has an empty or missing `type` field')
        
        self.__is_registered(enttype)
        
        T     = self.__registered.get(enttype)
        entry = self.__foreign_keys(T(**entry))
        
        return entry if not isinstance(entry, Tag) else entry.data
        
    # set database entry by key
    def __setitem__(self, eid:str, entry:Entry) -> None:
        # entry must be a registered Entry subclass
        self.__is_registered_entry(entry)
        
        if entry.id is UNIQUE:
            entry.id = self.next_id(entry.type)
            
        eid = entry.unique if eid is UNIQUE else eid
            
        # store entry in database as dictionary
        with shelve.open(self._db) as db:
            db[f'{eid}'] = entry.asdict
            
    # delete database entr(y|ies) by key(s)
    # all deleted items are stored locally until the app is closed, the bin is emptied or a subclass manually deletes a bin key
    def __delitem__(self, eids:Iterable) -> None:
        eids = list(map(str, eids)) if isinstance(eids, list|tuple|set) else (f'{eids}',)
        with shelve.open(self._db) as db:
            for eid in eids:
                if (entry := db.get(eid)): 
                    self.__session_bin[eid] = entry
                    
                    del db[eid]

    # PRIVATE UTILS
    
    # all Entry subclasses must be registered with a unique `.TYPE`
    def __register_type(self, entry_cls:type) -> None:
        try   : C = entry_cls.TYPE
        except: ...
        else  :
            if C not in self.__registered:
                self.__registered[C] = entry_cls
    
    def __is_registered(self, enttype:str):
        if f'{enttype}' not in self.__registered:
            raise ValueError(f'{enttype} is not a registered type')
            
    def __is_registered_entry(self, entry:Entry):
        if not isinstance(entry, Entry):
            raise ValueError('The `entry` argument must be a derivitive of `Entry`')
            
        self.__is_registered(entry.type)
    
    def __entry(self, entry:Any, conditions:str, cast:bool=True) -> Entry:
        if isinstance(entry, Entry):
            raw = entry.asdict
            
            if Query.check_conditions(raw, conditions):
                return entry if cast else raw
                
        return None
        
    # get registered entry type or default to "all"
    def __enttype(self, enttype:str|None) -> str:
        if enttype:
            try   : self.__is_registered(enttype)
            except: enttype = None
        return enttype or Entry.TYPE 
    
    # whack-a-mole: default or custom filename for zip backup    
    def __zippath(self, name:str|None=None) -> str:
        return f'{self._db}.{self.ZIP_EXT}' if not name else os.path.abspath(os.path.join(DAT, f'{name}.{self.ZIP_EXT}'))
    
    # process all foreign keys for this entry
    def __foreign_keys(self, entry:Entry) -> Entry:
        self.__is_registered_entry(entry)
        
        for key in entry.foreign_keys:
            if fk := getattr(entry, f'fk_{key}', None):
                T = type(fk)
                
                for fk_key in (fk if isinstance(fk, list|tuple) else (f'{fk}', )):
                    # if fk_key is a query, store query results
                    if results := [result for result in self.query_all(fk_key)]:
                        setattr(entry, key, results)
                    # else try fk_key as 1 or more keys
                    else:
                        if not (value := self.exists(fk_key)): 
                            raise KeyError(f'{fk_key} does not exist in the database')
                            
                        if isinstance(fk, list|tuple):
                            targ = getattr(entry, key, (t := T())) or t # `or t` - entry.key could be None
                            targ = T((*targ, value))
                            setattr(entry, key, targ)
                        elif isinstance(fk, str):
                            setattr(entry, key, T(value))
                        else:
                            raise ValueError(f'{T} must be list, tuple, or str')
                        
        return entry
        
    # EMULATORS  
        
    # get database keys from entries of type=enttype
    def keys(self, enttype:str|None=None) -> Iterator:
        enttype = self.__enttype(enttype)
        
        with shelve.open(self._db) as db:
             for key in db.keys():
                if enttype in (Entry.TYPE, db[key].get('type')):
                    yield key
      
    # get database values from entries of type=enttype
    # True|False - cast entry to type
    def values(self, enttype:str|None=None, cast:bool=True) -> Iterator:
        for eid in self.keys(enttype):
            # this will not be an Entry, only if it was a Tag
            # Tag is always returned as it's `.data`
            if isinstance((entry := self[eid]), Entry) and not cast:
                entry = entry.asdict
                
            yield entry
      
    # get database items from entries of type=enttype
    # True|False - cast entry to type
    def items(self, enttype:str|None=None, cast:bool=True) -> Iterator:
        for eid in self.keys(enttype):
            # this will not be an Entry, only if it was a Tag
            # Tag is always returned as it's `.data`
            if isinstance((entry := self[eid]), Entry) and not cast:
                entry = entry.asdict
                
            yield eid, entry
            
    # RESETS
         
    # empty session bin
    def empty_bin(self) -> None:
        del self.__session_bin
        self.__session_bin = dict()
    
    # (overwrite|create) empty database
    def wipe(self) -> None:
        with shelve.open(self._db, flag='n'):
            ...  
            
    # TRANSFORMERS
    
    # sort entries by type and id
    def sort(self, backup:bool=True):
        if backup: self.backup('before_sort')
        
        results = dict()
        for T in (*self.TYPES, Tag):
            if entries := self.todict(T.TYPE):
                items = sorted(entries.items(), key=lambda it: it[-1].get('id'))
                results.update(dict(items))
            
        #print(json.dumps(results, indent=4))
        self._dict2db(results, True)
        
    # all database entries of `.type`==enttype as dictionary
    def todict(self, enttype:str|None=None) -> dict:
        enttype = self.__enttype(enttype)
        results = dict()
        
        if enttype == Tag.TYPE:
            with shelve.open(self._db) as db:
                results.update({k:v for k,v in db.items() if enttype in (Entry.TYPE, v.get('type'))})
        else:
            results = dict(self.items(enttype, False))
            
            # if we are getting all entries, we have to manually get tags
            if enttype == Entry.TYPE:
                results.update(self.todict(Tag.TYPE))
            
        return results
     
    # dump database to zipped json without indent 
    def backup(self, name:str|None=None) -> None:
        with zf.ZipFile(self.__zippath(name), mode='w', compression=zf.ZIP_LZMA) as zip:
            zip.writestr('database.json', repr(self))
         
    # load database from zip file         
    def restore(self, name:str|None=None) -> None:
        path = self.__zippath(name)
        
        if not os.path.isfile(path):
            raise ValueError(f'{path} does not exist')
            
        with zf.ZipFile(path, mode='r') as zip:
            with zip.open('database.json') as file:
                self._dict2db(json.load(file), True)
            
    # include `data` in the database  
    # overwrite will completely wipe the database without saving
    def _dict2db(self, data:dict, overwrite:bool=False) -> None:
        if not data: return
        if not isinstance(data, dict):
            raise ValueError('The `data` argument must be of type dict[eid, Any]')
        
        flag = ('c','n')[overwrite]
        with shelve.open(self._db, flag=flag) as db:
            for eid, entry in data.items():
            
                if not (enttype := entry.get('type')):
                    raise ValueError('entry has an empty or missing `type` field')
                
                self.__is_registered(enttype)
                
                db[eid] = entry
               
    # FEATURES
    
    # get first entry matching query
    def exists(self, query:str, cast:bool=True) -> Entry|dict|None:
        try   : targ = self[query]
        except: targ = None
        else  : 
            if isinstance(targ, Entry) and not cast:
                targ = targ.asdict
                
        return targ
    
    #    
    def query_all(self, query:str, cast:bool=True) -> Iterator:
        if params := Query.params(query):
            typekey, conditions = params
            
            if entry := self.exists(typekey):
                if isinstance(entry, list|tuple|set):
                    for ent in entry:
                        if ent := self.__entry(ent, conditions, cast):
                            yield ent
                                
                elif entry := self.__entry(entry, conditions, cast):
                    yield entry
                            
            else:
                self.__is_registered(typekey)
                
                for entry in self.values(typekey):
                    if entry := self.__entry(entry, conditions, cast):
                        yield entry
    
    # get a count of enttype entries
    def count(self, enttype:str) -> int:
        return sum(1 for _ in self.keys(enttype))
        
    # get the next available id number for an enttype
    def next_id(self, enttype:str) -> int:
        m = -1
        
        # Tag is always returned as it's `.data` value
        # we have to be more direct if we want to read Tag ids
        if enttype == Tag.TYPE:
            with shelve.open(self._db) as db:
                m = max([m, *(x.get('id') for key in db.keys() if enttype == (x := db[key]).get('type'))]) + 1
        else:
            m = max([m, *(x.id for x in self.values(enttype))]) + 1
        return m
        
    # check if an id is available for an enttype
    def is_unique_id(self, enttype:str, uid:int) -> bool:
        return not self.exists(Entry.unique_format(enttype, uid))
        
    # only write this entry if it doesn't exist
    def make_once(self, eid:str|None, entry:Entry) -> bool:
        self.__is_registered_entry(entry)
            
        if not self.exists(eid or entry.unique):
            self[eid] = entry
            return True
            
        return False



