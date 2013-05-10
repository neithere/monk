Frequently Asked Questions
~~~~~~~~~~~~~~~~~~~~~~~~~~

What are the primary use cases of Monk?
---------------------------------------

…

Why would I want to use Monk?
-----------------------------

…

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
The :func:`~monk.validation.validate` function will convert the "natural"
declarations into rules; if it finds a ready-made rule, it just accepts it.

For example::

    spec = {
        'name': str,
        'age': int,
        'attrs': Rule(datatype=dict, optional=True, inner_spec={'foo': int})
    }

Do I need MongoDB to use Monk?
------------------------------

**No.**
Monk comes with a MongoDB extension but since v.0.6 the dependency is optional.

Is Monk stable enough?
----------------------

**It depends** on requirements.  Feel free to use Monk in personal apps and
prototypes.  Avoid using it in production until v.1.0 is out (or expect minor
changes in the API and therefore ensure good coverage of your code).

:quality:
    More than 90% of code is covered by tests.  The key modules are fully
    covered.

:stability:
    The API is still evolving but the core is considered stable since v.0.7.
    Even serious changes under the hood barely affect the public interface.

