Frequently Asked Questions
~~~~~~~~~~~~~~~~~~~~~~~~~~

What are the primary use cases of Monk?
---------------------------------------

* Entity schema for schema-less data storages
  (NoSQL, JSON, YAML, CSV, whatever)
* Publish/get data via RESTful API
* Safely implement ETL
* Process user input
* ODMs (object-document wrappers) as syntax sugar upon Monk

Why would I want to use Monk?
-----------------------------

Monk allows to quickly prototype schemata using plain Python structures.
It is very powerful, flexible, transparent and unobtrusive; all the power
is accessible through a few functions and the rule class (which you may not
even notice unless your use cases are demanding enough).  It is possible
to write a simple script, build a large project or a library upon Monk.

If in doubt, I encourage you to use Monk.  If it's not enough, read the docs
and make sure you squeeze the maximum from the rules.

When *not* to use Monk?  Easy: when the case is particularly complex, major
additions should be done but a dedicated tool already exists.  For instance,
it is possible to build an alternative to WTForms upon Monk but why?
Well, who knows.

What problems does Monk solve?
------------------------------

* Validation of arbitrary data
* Populating incomplete documents with regard to a schema
* Defining schemata in a universal way for different backends
* Keeping it simple

How does Monk solve these problems?
-----------------------------------

1. defines two mutually complementary schema conventions:

   * :term:`natural spec` (simple and pythonic)
   * :term:`detailed spec` (more verbose and powerful)

2. validates data against specs;

3. manipulates data with regard to specs;

4. provides an optional ODM for MongoDB based on the above-mentioned features.

Is Monk a standalone tool or a building block for ODMs?
-------------------------------------------------------

**Both.**

Monk ships with an integrated MongoDB ODM.  It's usable and can serve
as an example of how ODMs can be built upon Monk.

In many cases ODM is not needed at all; the validation and manipulation
features of Monk are enough even for complex applications.

Is Monk validation usable only for documents?
---------------------------------------------

**No.**
It is possible to validate any value, be it a string, a number, a custom class
instance or a full-blown document with multiple nested dictionaries.

Why are there two ways of schema declaration?
---------------------------------------------

The "natural" way is intuitive and requires very little knowledge about how
Monk works.  It's about using plain Python data types to design a template
for the value.  The resulting declaration is clear and readable.

The "verbose" way is less readable, involves more boilerplate code and requires
additional knowledge.  However, this approach enables fine-tuning and inline
customization that the "natural" way cannot achieve.

To sum up: a quick start with complexity evolving along with the needs.

Can I mix the "natural" and "verbose" declarations?
---------------------------------------------------

**Yes.**
The :func:`~monk.helpers.validate` function will convert the "natural"
declarations into rules; if it finds a ready-made rule, it just accepts it.

For example:

.. code-block:: python

    spec = {
        'name': str,
        'age': IsA(int, default=18) | Equals(None),
        'attrs': [IsA(str) | IsA(int) | NotExists()]
    }

    validate(spec, { ... your data goes here ... })

The validators can be combined with other validators or with non-validators;
in the latter case the right-hand value is first translated to a validator:

.. code-block:: python

    >>> full = (InRange(0,9) & IsA(int)) | IsA(str, default='unknown')
    >>> brief = InRange(0,9) & int | 'unknown'
    >>> full == brief
    True

Of course the technique only works if the left-hand value is a validator.

Which notation should I prefer?
-------------------------------

The one that's more readable in given use case.

Consider these alternative notations::

    IsA(str, default='foo')

    'foo'

The second one is definitely more readable.  But if the schema is mostly
written in verbose notation, adding bits in the natural one may increase
confusion::

    (IsA(int) | IsA(float)) & InRange(0,5) | IsA(str)

    (IsA(int) | float) & InRange(0,5) | str

    # the last one is cleaner and shorter but the mind fails to correctly
    # group the items using visual clues

When in doubt, stick to the Zen of Python!

It's also worth noting that natural specs are anyway translated to verbose
specs, so if you happen to generate the specs a lot, skip the additional layer.
Or, even better, build the schema once (including translation) and only
call the resulting validator for every value.

How "Natural" Declarations Map To "Verbose" Style?
--------------------------------------------------

In most cases the "natural" style implies providing a class or instance.

A **type or class** means that the value must be an instance of such:

=========== ==========================
natural     verbose
=========== ==========================
``int``     ``IsA(int)``
``str``     ``IsA(str)``
``list``    ``IsA(list)``
``dict``    ``IsA(dict)``
``MyClass`` ``IsA(MyClass)``
=========== ==========================

An **instance** means that the value must be of the same type (or an instance
of the same class) *and* the spec is the default value:

================ ================================================
natural          verbose
================ ================================================
``5``            ``IsA(int, default=5)``
``'hello'``      ``IsA(str, default='hello')``
``[]``           ``ListOf([])``
``{}``           ``DictOf([])``
``MyClass('x')`` ``IsA(MyClass, default=MyClass('x'))``
================ ================================================

Note that the `dict`, `list` and `MyClass` specs describe containers.
It is possible to nest other specs inside of these.  Not all containers are
handled by Monk as such: only `dict` and `list` are supported at the moment.
However, it all depends on validators and it's possible to write a validator
and drop it into any place in the spec.
Such validators are the building blocks for complex multi-level schemata.
If the "natural" spec is a non-empty container,
the :func:`~monk.validators.translate` function wraps it in a relevant
validator using its special requirements:

================ ============================================================
natural          verbose
================ ============================================================
``[str]``        ``ListOf(IsA(str))``
``{str: int}``   ``DictOf([ (IsA(str), IsA(int) ])``
================ ============================================================

.. note:: On defaults as dictionary keys

   **WARNING: THIS SECTION APPLIES TO v0.12 BUT IS OUT OF DATE AS OF v0.13**

   **TODO: UPDATE**

   Normally default values are only used in *manipulation*.
   In dictionaries they are also important for *validation*.  Consider this::

       spec_a = {str: int}
       spec_b = {'a': int}

   The spec `spec_a` defines a dictionary which may contain any number of keys
   that must be of type ``type('a')`` → `str`.

   The spec `spec_b` requires that the dictionary contains a single key ``'a'``
   and nothing else.  So, `a` in this case is not a default value but rather
   a precise requirement.

   The keys may be marked as optional and be multiple::

       spec_c = {'a': int, optional('b'): float}

   It's also possible to allow arbitrary keys of different types::

       spec_d = {str: int, tuple: float}

   Of course the key datatype must be hashable.

.. note:: On optional dictionary keys vs. values

   **WARNING: THIS SECTION APPLIES TO v0.12 BUT IS OUT OF DATE AS OF v0.13**

   **TODO: UPDATE**

   Consider this spec::

       spec_a = {
           'a': int,
           'b': optional(int),
           optional('c'): int,
           optional('d'): optional(int),
       }

   It should not be surprising that the inner specs are interpreted thusly:

   :a: key must be present; value must be of `int` type
   :b: key must be present; value must be of `int` type or may be `None`
   :c: key may exist or not; if yes, the value must be of `int` type
   :d: key may exist or not; value must be of `int` type or may be `None`

Do I need MongoDB to use Monk?
------------------------------

**No.**
Monk comes with a MongoDB extension but since v.0.6 the dependency is optional.

Does Monk support DBRefs and other MongoDB features?
----------------------------------------------------

**Yes.**
However, there's room for improvement.  Feel free to submit your use cases.

Is Monk stable enough?
----------------------

**It depends** on requirements.  Feel free to use Monk in personal apps and
prototypes.  Avoid using it in production until v1.0 is out (or expect minor
changes in the API and therefore ensure good coverage of your code).

:quality:
    More than 90% of code is covered by tests.  The key modules are fully
    covered.

:stability:
    The API is still evolving but the core was considered stable since v0.7.
    Even serious changes under the hood barely affect the public interface.

    Even after v0.13 featured a complete rewrite, the top-level API (the
    "natural" notation) was almost intact.

What are the alternatives?
--------------------------

See :doc:`similar`.
