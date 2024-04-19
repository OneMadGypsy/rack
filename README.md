# rack - if this document seems incomplete it's because I am writing it right now. there is a LOT to explain
A shelve wrapper that adds the following features:

1) dictionary behavior (`db.keys()`, `db.values()`, `db.items()`, `db[id or query]`)
2) foreign keys
3) queries
4) sort
5) backup (as json in a zip)
6) restore (from zipped json)
7) integration with `dataclasses`
8) numerous syntax tricks and implied behavior

The usage of this package starts with extending the `Entry` class and modifying your extension with the fields that you want to store in your database. There is no way around this. All database entry data is checked if it is an instance of `Entry` and then further checked if your `Entry` subclass is registered. Subclasses of `Entry` must overwrite the `TYPE` constant with a unique name. This name is used to register the custom entry, as well as create a unique name for it to be accessed by. Here is a simple example of a custom database entry.

```python3
from rack import Entry

@dataclass
class Book(Entry):
    TYPE = "book"

    title:str
    author:str
    rating:int = 0
```

