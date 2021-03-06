~~~~
Monk
~~~~

.. image:: https://img.shields.io/coveralls/neithere/monk.svg
    :target: https://coveralls.io/r/neithere/monk

.. image:: https://img.shields.io/travis/neithere/monk.svg
    :target: https://travis-ci.org/neithere/monk

.. image:: https://img.shields.io/pypi/format/monk.svg
    :target: https://pypi.python.org/pypi/monk

.. image:: https://img.shields.io/pypi/status/monk.svg
    :target: https://pypi.python.org/pypi/monk

.. image:: https://img.shields.io/pypi/v/monk.svg
    :target: https://pypi.python.org/pypi/monk

.. image:: https://img.shields.io/pypi/pyversions/monk.svg
    :target: https://pypi.python.org/pypi/monk

.. image:: https://img.shields.io/pypi/dd/monk.svg
    :target: https://pypi.python.org/pypi/monk

An unobtrusive data modeling, manipulation and validation library.

Supports MongoDB out of the box. Can be used for any other DB (or even without one).

Installation
------------

    $  pip install monk

Dependencies
------------

`Monk` is tested against the following versions of Python:

* CPython 2.6, 2.7, 3.2, 3.5
* PyPy 2.0

Optional dependencies:

* The MongoDB extension requires `pymongo` ≥ 3.0 (older may work too).

Documentation
-------------

See the complete `documentation`_ for details.

Examples
--------

Modeling
........

The schema is defined as a template using native Python data types:

.. code-block:: python

    # we will reuse this structure in examples below

    spec = {
        'title': 'Untitled',
        'comments': [
            {
                'author': str,
                'date': datetime.datetime.utcnow,
                'text': str
            }
        ],
    }

You are free to design as complex a document as you need.
The `manipulation` and `validation` functions (described below) support
arbitrary nested structures.

When this "natural" pythonic approach is not sufficient, you can mix it with
a more verbose notation, e.g.:

.. code-block:: python

    title_spec = IsA(str, default='Untitled') | Equals(None)

There are also neat shortcuts:

.. code-block:: python

    spec = {
        'url': nullable(str),
        'status': one_of(['new', 'in progress', 'closed']),
        'comments': [str],
        'blob': None,
    }

This could be written a bit more verbosely:

.. code-block:: python

    spec = {
        'url': IsA(str) | Equals(None),
        'status': Equals('new') | Equals('in progress') | Equals('closed'),
        'comments': ListOf(IsA(str)),
        'blob': Anything(),
    }

It is even possible to define schemata for dictionary keys:

.. code-block:: python

    CATEGORIES = ['books', 'films', 'toys']
    spec = {
        'title': str,
        opt_key('price'): float,    # key is optional; value is mandatory
        'similar_items': {
            one_of(CATEGORIES): [    # suggestions grouped by category
                {'url': str, 'title': str}
            ],
        }
    }

    # (what if the categories should be populated dynamically?
    #  well, the schema is plain Python data, just copy/update on the fly.)

And, yes, you can mix notations.  See FAQ.

This very short intro shows that Monk requires almost **zero learning to
start** and then provides very **powerful tools when you need them**;
you won't have to rewrite the "intuitive" code, only augment complexity
exactly in places where it's inevitable.

Validation
..........

The schema can be used to ensure that the document has correct structure
and the values are of correct types.

.. code-block:: python

    from monk.validation import validate

    # correct data: staying silent

    >>> validate(spec, data)

    # a key is missing

    >>> validate(spec, {'title': 'Hello'})
    Traceback (most recent call last):
       ...
    MissingKeys: must have keys: 'comments'

    # a key is missing in a dictionary in a nested list

    >>> validate(spec, {'comments': [{'author': 'john'}]}
    Traceback (most recent call last):
       ...
    DictValueError: 'comments' value item #0: must have keys: 'text', 'date'


    # type check; also works with functions and methods (by return value)

    >>> validate(spec, {'title': 123, 'comments': []})
    Traceback (most recent call last):
        ...
    DictValueError: 'title' value must be str

Custom validators can be used.  Behaviour can be fine-tuned.

The `validate()` function translates the "natural" notation to a validator
object under the hood.  To improve performance you can "compile" the validator
once (using `translate()` function or by creating a validator instance in place)
and use it multiple times to validate different values:

.. code-block:: python

    >>> from monk import *
    >>> translate(str) == IsA(str)
    True
    >>> validator = IsA(str) | IsA(int)
    >>> validator('hello')
    >>> validator(123)
    >>> validator(5.5)
    Traceback (most recent call last):
        ...
    AllFailed: must be str or must be int

Manipulation
............

The same schema can be used to create full documents from incomplete data.

.. code-block:: python

    from monk import merge_defaults

    # default values are set for missing keys

    >>> merge_defaults(spec, {})
    {
        'title': 'Untitled',
        'comments': [],
    }

    # it's easy to override the defaults

    >>> merge_defaults(spec, {'title': 'Hello'})
    {
        'title': 'Hello',
        'comments': [],
    }

    # nested lists of dictionaries can be auto-filled, too.
    # by the way, note the date.

    >>> merge_defaults(spec, {'comments': [{'author': 'john'}]})
    {
        'title': 'Untitled',
        'comments': [
            {
                'author': 'john',
                'date': datetime.datetime(2013, 3, 3, 1, 8, 4, 152113),
                'text': None,
            }
        ]
    }

Object-Document Mapping
-----------------------

The library can be also viewed as a framework for building ODMs
(object-document mappers).  See the MongoDB extension and note how it reuses
mixins provided by DB-agnostic modules.

Here's an example of the MongoDB ODM bundled with Monk:

.. code-block:: python

    from monk.mongo import Document

    class Item(Document):
        structure = {
            'text': unicode,
            'slug': unicode,
        }
        indexes = {
            'text': None,
            'slug': {'unique': True},
        }

    # this involves manipulation (inserting missing fields)
    item = Item(text=u'foo', slug=u'bar')

    # this involves validation
    item.save(db)

Links
-----

* `Project home page`_ (Github)
* `Documentation`_ (Read the Docs)
* `Package distribution`_ (PyPI)
* Questions, requests, bug reports, etc.:

  * `Issue tracker`_
  * Direct e-mail (neithere at gmail com)

.. _project home page: http://github.com/neithere/monk/
.. _documentation: http://monk.readthedocs.org
.. _package distribution: http://pypi.python.org/pypi/monk
.. _issue tracker: http://github.com/neithere/monk/issues/

Author
------

Originally written by Andrey Mikhaylenko since 2011.

Please feel free to submit patches, report bugs or request features:

    http://github.com/neithere/monk/issues/

Licensing
---------

Monk is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Monk is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with Monk.  If not, see <http://gnu.org/licenses/>.
