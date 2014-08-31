Similar Projects
~~~~~~~~~~~~~~~~

Below is a list of projects that share one or more major goals with Monk.

The descriptions may be a bit too critical, but that's only because of the
inevitable competition between Monk and these projects; Monk aims to be better
and the list shows how it is better.  I mean, what's the point of creating
a project if not to make a solution that would incorporate the strong points
and address the weaknesses of its predecessors?  Oh well.

.. note:: Spotted an error?

   Please excuse me for possible false assumptions about the projects being
   described; if you find an error, please don't hesitate to poke me via e-mail
   or the issue tracker (as this would be a proper documentation issue).

Schema Definition
-----------------

**Monk**
  See :mod:`monk.schema`.

MongoKit_
  Simple and pythonic, very similar to Monk (actually, Monk's "natural" DSL was
  inspired by that of MongoKit).  However, everything is tightly bound to
  MongoDB (not to mention the lacking possibility to work with plain data
  without ODMs); the required flag, default values and custom validators are
  defined on the root level, duplicating the structure in each case.

  MongoKit example::

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

      Spec(**data).validate()

  Semantically equivalent schema in Monk (without classes)::

      spec = {
          'foo': 5,
          'bar': nullable(str),
          'baz': {
              'quux': 'flux'
          }
      }

      validate(spec, data)

  Very similar support (and notation) for nested lists and dicts; also supports
  nested tuples.

MongoEngine_
  Very verbose Django-like syntax, traditional for ORMs.

  MongoEngine example::

      class User(Document):
          name = StringField(required=True)

      class Comment(EmbeddedDocument):
          author = ReferenceField(User, required=True)
          content = StringField(required=True, max_length=30)
          added = DateTimeField(required=True, default=datetime.datetime.utcnow)

      class Post(Document):
          title = StringField(required=True)
          author = ReferenceField(User)
          tags = ListField(StringField())
          comments = ListField(EmbeddedDocumentField(Comment))

  Semantically equivalent schema in Monk (without classes)::

      user_schema = {'name': str}

      comment_schema = {
          'author': ObjectId,   # see monk.modeling; still needs work
          'content': IsA(str) & Length(max=30),
          'added': datetime.datetime.utcnow,
      }

      post_schema = {
          'title': str,
          'author': ObjectId,
          'tag': [ optional(str) ],
          'comments': [ optional(comment_schema) ]
      }

  The `FooField` layer can be added on top of the normal Monk syntax if needed.

  MongoEngine is tightly bound to MongoDB and provides many database-specific
  features which are not present in Monk (e.g. defining deletion policy of
  referred documents).

Colander_
  Declarative and imperative schema declaration (for "static" and dynamically
  generated data models).  Very verbose, class-based.  Similar to traditional
  ORMs but more flexible and generalized: there are tuple/mapping/sequence
  schemata with nested "schema nodes" and/or other schemata.  Supports
  inheritance.

  Colander example (from tutorial)::

      import colander

      class Friend(colander.TupleSchema):
          rank = colander.SchemaNode(colander.Int(),
                                     validator=colander.Range(0, 9999))
          name = colander.SchemaNode(colander.String())

      class Phone(colander.MappingSchema):
          location = colander.SchemaNode(colander.String(),
                                         validator=colander.OneOf(['home', 'work']))
          number = colander.SchemaNode(colander.String())

      class Friends(colander.SequenceSchema):
          friend = Friend()

      class Phones(colander.SequenceSchema):
          phone = Phone()

      class Person(colander.MappingSchema):
          name = colander.SchemaNode(colander.String())
          age = colander.SchemaNode(colander.Int(),
                                    validator=colander.Range(0, 200))
          friends = Friends()
          phones = Phones()

  Semantically equivalent schema in Monk (without classes)::

      from monk import Rule
      from monk import validators

      friend_schema = {
          'rank': IsA(int) & InRange(0, 9999),
          'name': str
      }
      phone_schema = {
          'location': IsA(str) & one_of(['home', 'work']),
          'number': str,
      }
      person_schema = {
          'name': str,
          'age': IsA(int) & InRange(0, 200),
          'friends': [ friend_schema ],
          'phones': [ phone_schema ],
      }

  .. note:: Tuples

     Monk does not support fixed-size tuples with named arguments out of the
     box.  However, it's easy to write a validator for this specific use case.

Validation
----------

**Monk**
  See :mod:`monk.validators`.

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

MongoEngine_
  Validation is integrated into `FooField` classes and triggered on save.
  Only very basic validators (required, unique, choices) are tunable. Custom
  validation implies custom field classes.  For each field.  Ouch.

Colander_
  A `SchemaNode` instance validates a value by a) the `SchemaType` bound
  to its class, and b) by an optional validator passed to the constructor
  (a selection of common validators is bundled in the `colander` module).

  It takes time to even grasp the terminology, not to mention the code (which
  is very clean and well-documented but presented as a 2K+ LOC module that
  handles all flavours of schema declaration + validation + serialization).

Manipulation
------------

**Monk**
  See :mod:`monk.manipulation`.

MongoKit_
  Data manipulation mostly embraces conversion between Python types and MongoDB
  internal representation (via PyMongo).  This can be tuned with "Custom Types"
  that handle both manipulation and validation.

  It is unknown whether the list of default values supports callables.

MongoEngine_
  Mostly embraces conversion between Python types and MongoDB.  This is always
  implemented by `FooField` classes that handle both manipulation and
  validation.

  Supports callable defaults.

Colander_
  Focused on (de)serialization (which is closer to normalization)::

      >>> class MySchema(colander.MappingSchema):
      ...     age = colander.SchemaNode(colander.Int())
      ...
      >>> schema = MySchema()
      >>> schema.deserialize({'age': '20'})
      {'age': 20}

  Supports optional `preparer functions`_ per node to prepare deserialized data
  for validation (e.g. strip whitespace, etc.).

  In general, this functionality is very useful (and not bound to a concrete
  storage backend).  Not sure if Monk should embrace it, though.

  `SchemaNode` also contains `utility functions`_ to manipulate an `appstruct`
  or a `cstruct`:

  * (un)flattening a data structure::

        >>> schema.flatten({'a': [{'b': 123}]})
        {'a.0.b': 123}

  * accessing and mutating nodes in a data structure::

        rank = schema.get_value(appstruct, 'friends.2.rank')
        schema.set_value(appstruct, 'friends.2.rank', rank + 5000)

    (which resembles the MongoDB document updating API)

  .. _preparer functions: http://docs.pylonsproject.org/projects/colander/en/latest/basics.html#preparing-deserialized-data-for-validation
  .. _utility functions: http://docs.pylonsproject.org/projects/colander/en/latest/manipulation.html

Modeling
--------

**Monk**
  See :mod:`monk.modeling`.

  :lightweight schema:
    Yes.  The schema is not bound to any kind of storage or form.
    It can be — just add another layer on top.

  :reusable parts:
    Yes.  The Document class can be used right away, subclassed or be built
    anew from the components that were designed to be reusable.

    This makes Monk a good building block for custom ODMs.

  :dot-expanded dictionary behaviour:
    Yes.

  :polymorphism (document inheritance):
    Not yet.

MongoKit_
  :lightweight schema:
    No.  The Document class is bound to a MongoDB collection.

  :reusable parts:
    No.  The underlying functions are not intended to be used separately.

  :dot-expanded dictionary behaviour:
    Yes.

  :polymorphism (document inheritance):
    Yes.

MongoEngine_
  :lightweight schema:
    No.  The Document class is bound to a MongoDB collection.

  :reusable parts:
    No.  The underlying functions are not intended to be used separately.

  :dot-expanded object behaviour:
    Yes.

  :polymorphism (document inheritance):
    Yes.

Colander_
  No modeling as such.

MongoDB extension
-----------------

**Monk**
  See :mod:`monk.mongo`.

MongoKit_
  Tightly bound to MongoDB on all levels.  The document class is bound to
  a collection (which I found problematic in the past but generally this may be
  good design).  Very good integration.  PyMongo is accessible when needed
  (like in Monk).  Keeps the data clean from tool-specific metadata (like Monk).
  In general, MongoDB support is superior compared to that of Monk but both use
  PyMongo so the basic functionality is exactly the same.  The choice depends
  on given project's use cases.

MongoEngine_
  Seems to be on par with MongoKit.

.. _MongoKit: http://namlook.github.io/mongokit/
.. _MongoEngine: https://mongoengine-odm.readthedocs.org
.. _Colander: http://docs.pylonsproject.org/projects/colander/en/latest/basics.html

