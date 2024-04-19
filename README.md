# rack - if you can read this I am expanding this document right now. I did not forget to delete this. right now means RIGHT NOW
A shelve wrapper that adds the following features:

1) dictionary behavior (`db.keys()`, `db.values()`, `db.items()`, `db[id or query]`)
2) foreign keys
3) foreign queries - this is a query that was placed in a foreign key
4) queries
5) sort
6) backup (as json in a zip)
7) restore (from zipped json)
8) integration with `dataclasses`
9) numerous syntax tricks and implied behavior

## Entries

The usage of this package starts with extending the `Entry` class and modifying your extension with the fields that you want to store in your database. There is no way around this. All database entry data is checked if it is an instance of `Entry` and then further checked if your `Entry` subclass is registered. Subclasses of `Entry` must overwrite the `TYPE` constant with a unique name. This name is used to register the custom entry, as-well-as create a unique name for it to be accessed by. Here is a simple example of a custom database entry.

```python3
from rack        import Database, Entry, Tag, Query, UNIQUE
from dataclasses import dataclass, field

@dataclass
class Book(Entry):
    TYPE = "book"

    title:str
    author:str
    rating:int = 0
```

You can make as many `Entry` sublasses as you need. The below is to imply that our database will include books and authors. You will notice that `Author` has a `fk_books` field. Prepending a field with `fk_` implies that the field will contain one or more foreign keys or a foreign query. I will go into more detail regarding foreign keys later in this documentation, but know that the `fk_` prefix is something that the database specifically looks for. You cannot use it arbitrarily.

```python3
from rack        import Database, Entry, Tag, Query, UNIQUE
from dataclasses import dataclass, field

@dataclass
class Book(Entry):
    TYPE = "book"

    title:str
    author:str
    rating:int = 0
    
    
@dataclass
class Author(Entry):
    TYPE = "author"
    
    name:str
    fk_books:list = field(default_factory=list)
```

## Tags

There is a special `Entry` subclass built-in named `Tag`. A tag is used to store arbitrary data that does not really qualify to be considered as an `Entry` subclass. It can also be used to store foreign keys or foreign queries. There is no reason to subclass `Tag`, and doing so actually defeats the purpose of `Tag`. `Tag` only has 2 fields: `data` and `fk_data`. You can store anything that can be serialized as JSON on the `data` field. Alternately, you can store one or more foreign keys or a foreign query in the `fk_data` field. If you set `fk_data` to anything at all `data` will be overwritten with the processed `fk_data` field. Tags have the special behavior that they are returned from the database as the value of `data`, instead of a `Tag` class. Below is an example of `Tag` usage and results. Please note that the syntax for this example is designed to be written in a way that you understand it. There is a MUCh better way to do this. We haven't covered that yet.

```python3
db['some_unique_key'] = Tag(0, fk_data=('book_0', 'book_1'))
print(db['some_unique_key'])
```
#### output
**note**: printing entries will always result in pretty-printed JSON, but `db['some_unique_key']` is actually a `list` of `Book` entries
```python3
{
    "id": 0,
    "type": "book",
    "title": "The B",
    "author": "A.B. Cee",
    "rating": 4
}
{
    "id": 1,
    "type": "book",
    "title": "E Up!",
    "author": "B.C. Dea",
    "rating": 4
}
```

## Database

The `Database` class is intended to be extended. Using it directly would be cumbersome as it only contains very general-purpose features. It is up to you to combine those features in a subclass to create more specific behavior. You must overwrite the `TYPES` constant with a `list|tuple` of the `Entry` subclasses that you want to register with the database. The order that you put these in will determine the order that database is sorted when `db.sort()` is called. Below is a bare-bones example of a `Database` subclass. `dbname` is the name that your database will be created and accessed with. Setting `wipe` to `True` will completely erase your database and create a new empty database. You will **NOT** be asked or warned if you really want to do this.

```python3
from rack        import Database, Entry, Tag, Query, UNIQUE
from dataclasses import dataclass, field

class Library(Database):
    TYPES = Author, Book
    
    def __init__(self, wipe:bool=False) -> None:
        Database.__init__(self, dbname='library', wipe=wipe)
```

## Queries
Queries have the syntax `TYPE or Unique Name: Semi-colon separated Conditions`. If we use the `Book` entry above an example query could be `'book: author <%. "D"; title <%. "T"'`. This example would give the results of every book by an author that starts with (`<%`) "D", having a title that starts with "T", using a lowercase (`.`) comparison. The allowed datatypes in a query are `float`, `int`, `bool`, `str` and `list`. The syntax for each are as follows:

| type    | example          |
| ------- | ---------------- |
| `float` | 3.14             |
| `int`   | 42               |
| `bool`  | True             |
| `str`   | "in quotes"      |
| `list`  | comma, separated |

There are a number of comparison operators. Most of them are well-known and obvious. I invented a few that are not obvious, at all. Here is a table that explains all of the operators.

| op | description                                |
| -- | ------------------------------------------ |
|!->.| not in using lowercase comparison          |
|!<%.| not starts with using lowercase comparison |
|!%>.| not ends with using lowercase comparison   |
|!=. | not equal using lowercase comparison       |
|->. | in using lowercase comparison              |
|<%. | starts with using lowercase comparison     |
|%>. | ends with using lowercase comparison       |
|==. | equals using lowercase comparison          |
|!-> | not in                                     |
|!<% | not starts with                            |
|!%> | not ends with                              |
|!=  | not equals                                 |
|->  | in                                         |
|<%  | starts with                                |
|%>  | ends with                                  |
|==  | equals                                     |
|=>  | is (entirely useless for this)             |
|<=  | less-than equals                           |
|>=  | greater-than equals                        |
|<   | less-than                                  |
|>   | greater-than                               |
