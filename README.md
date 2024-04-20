# rack

A `shelve` wrapper that adds numerous useful features. This documentation is a work-in-progress. I need a little more time to flesh everything out, and then refactor/reorganize everything to be a cohesive unit with a progressing flow. Pretty much everything that can be done is either illustrated or mentioned. I apologize if anything is written confusingly or poorly. I assure you that I care about my project and hope to have this documentation in order soon.

1) dictionary behavior (`db.keys()`, `db.values()`, `db.items()`, `db[id or query]`)
2) foreign keys
3) foreign queries - this is a query that was placed in a foreign key
4) queries
5) sort
6) backup (as json in a zip)
7) restore (from zipped json)
8) integration with `dataclasses`
9) numerous syntax tricks and implied behavior

## Overview

### Entries

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

`Entry` extends a mixin that adds a bunch of features to dataclasses. Most of the features allow dataclasses to be treated like a `dict`. While I am fleshing out all of this documentation I do not believe it is immediately important to describe all of the possibilities. If you want to discover them yourself, simply go to `mixins.py` and look at the `Dataclass_mi` class. I will revisit this section after I have documented the more important features of my package, and go into greater detail of all of the possibilities. For the most basic overview, assuming `entry` is an instance of `Entry` (or `Entry` subclass), the following is possible:

1) `entry.keys()`
2) `entry.values()`
3) `entry.items()`
4) `**entry`
5) `print(entry)` - pretty-printed JSON representation of entry
6) `entry.kwargs('some_field', 'some_other_field')` returns `{'some_field': value1, 'some_other_field': value2}`
7) `entry.args('some_field', 'some_other_field')` returns `[value1, value2]`
8) `entry(...)` - has complex behavior, I'll explain later

--------

### Tags

There is a special `Entry` subclass built-in named `Tag`. A tag is used to store arbitrary data that does not really qualify to be considered as an `Entry` subclass. It can also be used to store foreign keys or a foreign query. There is no reason to subclass `Tag`, and doing so actually defeats the purpose of `Tag`. `Tag` only has 2 fields: `data` and `fk_data`. You can store anything that can be serialized as JSON on the `data` field. Alternately, you can store one or more foreign keys or a foreign query in the `fk_data` field. If you set `fk_data` to anything at all, `data` will be overwritten with the processed `fk_data` results. Tags have the special behavior that they are returned from the database as the value of `data`, instead of a `Tag` class. Below is an example of `Tag` usage and results. Please note that the syntax for this example is designed to be written in a way that you understand it. There is a MUCH better way to do this. We haven't covered that yet.

```python3
db['some_unique_key'] = Tag(0, fk_data=('book_0', 'book_1'))
print(db['some_unique_key'])
```
#### output
**note**: printing `Entry` types will always result in pretty-printed JSON, but `db['some_unique_key']` is actually a `list` of `Book` entries, in this case. Of course the example below is just illustratory and you aren't going to magically have entries in your database that you never created. However, `id` and `type` fields will always be present in your entries as they are built into the `Entry` class, and are mandatory for any of this to work in the first place.
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

--------

### Database

The `Database` class is intended to be extended. Using it directly would be cumbersome as it only contains very general-purpose features. It is up to you to combine those features in a subclass to create more specific behavior. You must overwrite the `TYPES` constant with a `list|tuple` of the `Entry` subclasses that you want to register with the database. The order that you put these in will determine the order that database is sorted when `db.sort()` is called. Below is a bare-bones example of a `Database` subclass. `dbname` is the name that your database will be created and accessed with. Setting `wipe` to `True` will completely erase your database and create a new empty database. You will **NOT** be asked or warned if you really want to do this.

```python3
from rack        import Database, Entry, Tag, Query, UNIQUE
from dataclasses import dataclass, field

class Library(Database):
    TYPES = Author, Book
    
    def __init__(self, wipe:bool=False) -> None:
        Database.__init__(self, dbname='library', wipe=wipe)
```

--------

### Queries
Queries have the syntax `TYPE or Unique Name: Semi-colon separated Conditions`. If we use the `Book` entry above, an example query could be `'book: author <%. "D"; title <%. "T"'`. This example would give the results of every book by an author that starts with (`<%`) "D", having a title that starts with "T", using a lowercase (`.`) comparison. The allowed datatypes in a query are `float`, `int`, `bool`, `str` and `list`. The syntax for each are as follows:

| type    | example          |
| ------- | ---------------- |
| `float` | 3.14             |
| `int`   | 42               |
| `bool`  | True             |
| `str`   | "in quotes"      |
| `list`  | comma, separated |

There are a number of comparison operators. Most of them are well-known and obvious. I invented a few that are not obvious, at all. Below is a table that explains all of the operators. Note that chaining operators in a manner that is logical is allowed ex: `book: 3 <= rating <= 5`. In this example `rating` is a field of `Book`, and it will be replaced with the `rating` value of the book instance that is currently being processed.

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

--------

### UNIQUE

`UNIQUE` is a sentinel value that indicates to the database to basically figure out what an `id` should be for you or to use the `.unique` property of the assigned value, depending on context. For full transparency, `UNIQUE` is just an alias for `dataclasses.MISSING`. Below illustrates the behavior of `UNIQUE`.

```python3
# this would store the book in the database under the key "book_0" or more specifically f'{Book.TYPE}_{book_instance.id}'
db[UNIQUE] = Book(0, title="some title", author="some author")

# this would do the same as above, but first it would find the next available id for the book instance
# please note that using this version will traverse the ENTIRE database, skipping everything that is not a `Book`,...
# find the highest `book_instance.id`, and add 1
db[UNIQUE] = Book(UNIQUE, title="some title", author="some author")
```

## Specifics

We have covered all of the most basic facts and usage of every available `rack` import. The following information will include the "meat and potatoes" of the specific usages of this package. There are numerous tricks and intracacies. I intend to illustrate all of them. Let's start with queries.

### Queries

The `Query` module is designed to concoct and parse queries. From the parsing perspective there isn't anything for you to be concerned with. Parsing is built into the database and is triggered automatically as it is necessary. For concocting queries you will want to use `Query.statement`. `Query.statement` does all of the boilerplate for you. You simply supply all of the proper arguments in a pythonic way, and it will combine and format it into a query that `Database` understands. Queries can get really ugly and manually creating them can easily become a chore full of mistakes. There is absolutely no reason to manually write queries. There isn't even a reason to understand how to manually write queries. My system is fully capable of doing this for you. Expanding upon our `Library` class we can easily illustrate how to create prepared statements. For the below example we are going to pretend that a bunch of books magically exist. I will flesh out more complete examples as we get further along. For now, let's work with a gist that focuses on what we are trying to illustrate.

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


class Library(Database):
    TYPES = Author, Book
    
    @staticmethod # kwargs example
    def unique_book(*args, **kwargs) -> str:
        conditions = 'author == {author} ; title == {title}'
        return Query.statement(Book.TYPE, conditions, *args, **kwargs)
    
    @staticmethod # args example   
    def rated_books(*args, **kwargs) -> str:
        conditions = '{} <= rating <= {} ; author -> {}'
        return Query.statement(Book.TYPE, conditions, *args, **kwargs)
        
    def __init__(self, wipe:bool=False) -> None:
        Database.__init__(self, dbname='library', wipe=wipe)


if __name__ == "__main__":
    db = Library()

    rate_query = Library.rated_books(2, 5, ('A.B. Cee', 'B.C. Dea'))

    # this will only make this Tag ONE time (as in forever), determining it's `id` ONE time
    # since `fk_data` is a query, the query will be run everytime this tag is requested from the database
    # the results of the query will overwrite `.data`, and requesting this tag will return the value of `.data` 
    db.make_once('book_rating', Tag(UNIQUE, fk_data=rate_query))

    # will return the results of the query, which will be a list of all the `Book` entries with a rating from 2 to 5, inclusive
    # by authors that are present in the supplied tuple of authors in the 3rd argument 
    print(db['book_rating'])

    # exact same concept as `rated_books` but we use kwargs instead of args
    unique_query = Library.unique_book(author="A.B. Cee", title="My Fist Book")

    # you can absolutely use a query for a database key
    # it's one of the main reasons I created this package
    print(db[unique_query])
```

--------

### Foreign Keys

Foreign keys are butt-simple. If we use my `Author` class from the above examples this is what can be expected:

1) upon committing an `Author` to the database, it will be saved "as-is"
2) upon retrieving it from the database, `.fk_books` will be processed and it's final data will be stored in a `.books` property. Whatever you put after `fk_` will be the name of the property that you can request the final data from

**note:** `.books` will not exist in the database. It is created on-the-fly when an author is requested from the database, and instanced as an `Author`. Of course this is on purpose. What is the point of the foreign keys if we store copies of all the `Book` entries on the `Author`?

```python3
# this is not wrong - db.__setitem__ returns and can be used as a right-side-expression
# which in this case will return the author with the id corrected from UNIQUE
ab_cee = db[UNIQUE] = Author(UNIQUE, name="A.B. Cee", fk_books=('book_0', 'book_5', 'book_17'))
print(ab_cee.books)
```

#### output

**reminder:** this is actually a list of `Book` instances, it just prints as JSON
```python3
{
    "id": 0,
    "type": "book",
    "title": "My Book",
    "author": "A.B. Cee",
    "rating": 1
}
{
    "id": 5,
    "type": "book",
    "title": "My Other Book",
    "author": "A.B. Cee",
    "rating": 2
}
{
    "id": 17,
    "type": "book",
    "title": "I Keep Writing Books!",
    "author": "A.B. Cee",
    "rating": 3
}
```

## Full Usage Example

```python3
from rack        import Database, Entry, Tag, Query, UNIQUE
from dataclasses import dataclass, field
from typing      import Iterable

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

       
class Library(Database):
    TYPES = Author, Book
    
    @property
    def book_count(self) -> int:
        return self.count(Book.TYPE)
        
    # format prepared statements  
    
    @staticmethod
    def unique_book(*args, **kwargs) -> str:
        conditions = 'author == {author} ; title == {title}'
        return Query.statement(Book.TYPE, conditions, *args, **kwargs)
    
    @staticmethod    
    def rated_books(*args, **kwargs) -> str:
        conditions = '{} <= rating <= {} ; author -> {}'
        return Query.statement(Book.TYPE, conditions, *args, **kwargs)
        
    @staticmethod    
    def author_name(*args, **kwargs) -> str:
        conditions = 'name == {}'
        return Query.statement(Author.TYPE, conditions, *args, **kwargs)
    
    @staticmethod    
    def author_startswith(*args, **kwargs) -> str:
        conditions = 'name <%. {}'
        return Query.statement(Author.TYPE, conditions, *args, **kwargs)
        
    def __init__(self, wipe:bool=False) -> None:
        # note: the database does not support write-back. You have to manually (re)save entries after modifying them
        Database.__init__(self, dbname='library', wipe=wipe)
            
    def add_books(self, books:Iterable) -> None:
        # `.next_id()` is a direct way to get the next available id
        for i, book in enumerate(books, self.next_id(Book.TYPE)):
            book = Book(i, **book)

            # note `book.kwargs` this is an example of one of the features listed at the end of the `Entry` section 
            book_query = Library.unique_book(**book.kwargs('title','author'))
            auth_query = Library.author_name(book.author)

            # this is how we test if entries exist before committing
            # it's a lower level equivalent to `.make_once()` where you have to determine what to do if it has never been made
            # `.exists()` returns the Entry if it does exist, which means it can have a dual purpose for retrieving a singular query result (the first match it finds)
            if not self.exists(book_query):
                if not (author := self.exists(auth_query)):
                    author = Author(UNIQUE, book.author)
                    
                if book.unique not in author.fk_books: 
                    author.fk_books.append(book.unique)
                    self[UNIQUE] = author              
                    
                self[UNIQUE] = book


if __name__ == "__main__":
    db = Library()

    # pretend all of this data came from scraping a website or similar data gathering technique 
    books = (dict(title="The A"         , rating=1, author="A.B. Cee"), 
             dict(title="The B"         , rating=4, author="A.B. Cee"), 
             dict(title="The C"         , rating=3, author="A.B. Cee"), 
             dict(title="The D"         , rating=2, author="A.B. Cee"), 
             dict(title="E Up!"         , rating=4, author="B.C. Dea"),
             dict(title="F It!"         , rating=8, author="B.C. Dea"), 
             dict(title="G For The Win!", rating=4, author="A.C. Ea" ), 
             dict(title="On H Street"   , rating=3, author="A.C. Ea" ))
             
    db.add_books(books)
    print('\nbook count:', db.book_count)

    # create a Tag (ONCE) on the database that holds a query to all of the books of a specified rating by specified authors
    rate_query = Library.rated_books(2, 5, ('A.B. Cee', 'B.C. Dea'))
    db.make_once('book_rating', Tag(UNIQUE, fk_data=rate_query))
    
    # query within the data of a tag
    # in this case: get all books from `rate_query` that specifically have a rating of 4
    # `.query_all(the_query)` is a generator
    q = Query.statement('book_rating', 'rating==4')
    for entry in db.query_all(q):
        print(entry)

    # sort the database
    # this really shouldn't be floating around where it happens every time the program is run
    # you should create conditions that determine whether or not it needs to be done
    db.sort()

    # backup the database
    # this can accept a `name` argument that sets the filename (without extension) for the backup
    # if no argument is supplied the backup will have the same filename as the database name
    # `.restore()` works the same way but in the opposite direction
    db.backup()

    # print the database as pretty-printed JSON
    print(db)

```
