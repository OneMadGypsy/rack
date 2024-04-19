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

#### Entries

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

You can make as many `Entry` sublasses as you need. The below is to imply that our database will include books and authors. You will notice that `Author` has a `fk_books` field. Prepending a field with `fk_` implies that the field will contain one or more foreign keys. I will go into more detail regarding foreign keys later in this documentation, but know that the `fk_` prefix is something that the database specifically looks for. You cannot use it arbitrarily.

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

#### Tags

There is a special `Entry` subclass built-in named `Tag`. A tag is used to store arbitrary data that does not really qualify to be considered an `Entry` subclass. It can also be used to store foreign keys or foreign queries. There is no reason to subclass `Tag`, and doing so actually defeats the purpose of `Tag`. There are exammples later in this document of `Tag Usage.

