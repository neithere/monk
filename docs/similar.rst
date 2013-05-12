Similar Projects
~~~~~~~~~~~~~~~~

Below is a list of projects that share one or more major goals with Monk.

The descriptions may be a bit too critical, but that's only because of the
inevitable competition between Monk and these projects; Monk aims to be better
and the list shows how it is better.  I mean, what's the point of creating
a project if not to make a solution that would incorporate the strong points
and address the weaknesses of its predecessors?  So, here we go.

Schema Definition
-----------------

MongoKit_
  Simple and pythonic, very similar to Monk (actually, Monk's "natural" DSL was
  inspired by that of MongoKit).  However, everything is tightly bound to
  MongoDB (not to mention the lacking possibility to work with plain data
  without ODMs); the required flag, default values and custom validators are
  defined on the root level, duplicating the structure in each case. Example::

      # Monk

      spec = {
          'foo': 5,
          'bar': optional(str),
          'baz': {
              'quux': 'flux'
          }
      }

      # MongoKit

      class Spec(Document):
          structure = {
              'foo': int,
              'bar': str,
              'baz': {
                  'quux': str
              }
          }
          default_values = {
              'foo': 5,
              'quux': 'flux'
          }
          required = ['foo', 'baz.quux']

  Very similar support (and notation) for nested lists and dicts; also supports
  nested tuples.

Validation
----------

MongoKit_
  Type validation (extensible with custom types).  All validators beyond types
  belong in a separate dictionary which mostly duplicates the schema dictionary.
  The list of required fields (with names in a MongoDB-ish dot notation, i.e.
  ``foo.$unicode.bar``) must be defined in yet another place.
  This approach implies noticeable redundancy for relatively complex documents.

  The Document class also has an overloadable ``validate()`` method which makes
  sense for simultaneous multi-field validation.  In Monk you would simply call
  the normal and a custom validation functions one after another (or overload
  the method in a similar way if using modeling).

Manipulation
------------

MongoKit_
  Data manipulation mostly embraces conversion between Python types and MongoDB
  internal representation (via PyMongo).  This can be tuned with "Custom Types"
  that handle both manipulation and validation.

  It is unknown whether the list of default values supports callables.

Modeling
--------

MongoKit_
  The Document class is bound to a MongoDB collection.  Supports dot-expanded
  dictionary behaviour (like Monk).  Supports polymorphism (Monk doesn't).
  The underlying functions are not intended to be used separately (in Monk this
  was one of the main design goals).

MongoDB extension
-----------------

MongoKit_
  Tightly bound to MongoDB on all levels.  The document class is bound to
  a collection (which I found problematic in the past but generally this may be
  good design).  Very good integration.  PyMongo is accessible when needed
  (like in Monk).  Keeps the data clean from tool-specific metadata (like Monk).
  In general, MongoDB support is superior compared to that of Monk but both use
  PyMongo so the basic functionality is exactly the same.  The choice depends
  on given project's use cases.

.. _MongoKit: http://namlook.github.io/mongokit/

