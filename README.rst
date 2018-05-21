*************************************************
environs: simplified environment variable parsing
*************************************************

.. image:: https://badge.fury.io/py/environs.svg
    :target: http://badge.fury.io/py/environs
    :alt: Latest version

.. image:: https://travis-ci.org/sloria/environs.svg?branch=master
    :target: https://travis-ci.org/sloria/environs
    :alt: Travis-CI

.. image:: https://img.shields.io/badge/marshmallow-3-blue.svg
    :target: https://marshmallow.readthedocs.io/en/latest/upgrading.html
    :alt: marshmallow 3 compatible

Environs is a Python library for parsing environment variables.

Environs is inspired by `envparse <https://github.com/rconradharris/envparse>`_ and uses `marshmallow <https://github.com/marshmallow-code/marshmallow>`_ under the hood for validating, deserializing, and serializing values.

Install
-------
::

    pip install environs

Basic usage
-----------

.. code-block:: python

    # export GITHUB_USER=sloria
    # export MAX_CONNECTIONS=100
    # export SHIP_DATE='1984-06-25'
    # export TTL=42
    # export ENABLE_LOGIN=true
    # export GITHUB_REPOS=webargs,konch,ped
    # export COORDINATES=23.3,50.0

    from environs import Env

    env = Env()
    # required variables
    gh_user = env('GITHUB_USER')  # => 'sloria'
    secret = env('SECRET')  # => raises error if not set

    # casting
    max_connections = env.int('MAX_CONNECTIONS')  # => 100
    ship_date = env.date('SHIP_DATE')  # => datetime.date(1984, 6, 25)
    ttl = env.timedelta('TTL')  # => datetime.timedelta(0, 42)

    # providing a default value
    enable_login = env.bool('ENABLE_LOGIN', False)  # => True
    enable_feature_x = env.bool('ENABLE_FEATURE_X', False)  # => False

    # parsing lists
    gh_repos = env.list('GITHUB_REPOS')  # => ['webargs', 'konch', 'ped']
    coords = env.list('COORDINATES', subcast=float)  # => [23.3, 50.0]


Supported types
---------------

The following are all type-casting methods of  ``Env``:

* ``env.str``
* ``env.bool``
* ``env.int``
* ``env.float``
* ``env.decimal``
* ``env.list`` (accepts optional ``subcast`` keyword argument)
* ``env.dict`` (accepts optional ``subcast`` keyword argument)
* ``env.json``
* ``env.datetime``
* ``env.date``
* ``env.timedelta`` (assumes value is an integer in seconds)
* ``env.url``
* ``env.uuid``


Handling prefixes
-----------------

.. code-block:: python

    # export MYAPP_HOST=lolcathost
    # export MYAPP_PORT=3000

    with env.prefixed('MYAPP_'):
        host = env('HOST', 'localhost')  # => 'lolcathost'
        port = env.int('PORT', 5000)  # => 3000

    # nested prefixes are also supported:

    # export MYAPP_DB_HOST=lolcathost
    # export MYAPP_DB_PORT=10101

    with env.prefixed('MYAPP_'):
        with env.prefixed('DB_'):
            db_host = env('HOST', 'lolcathost')
            db_port = env.int('PORT', 10101)


Proxied variables
-----------------

.. code-block:: python

    # export MAILGUN_LOGIN=sloria
    # export SMTP_LOGIN={{MAILGUN_LOGIN}}

    smtp_login = env('SMTP_LOGIN')  # =>'sloria'


Validation
----------

.. code-block:: python

    # export TTL=-2
    # export NODE_ENV='invalid'
    # export EMAIL='^_^'


    # simple validator
    env.int('TTL', validate=lambda n: n > 0)
    # => Environment variable "TTL" invalid: ['Invalid value.']

    # using marshmallow validators
    from marshmallow.validate import OneOf

    env.str('NODE_ENV',
            validate=OneOf(['production', 'development'],
                            error='NODE_ENV must be one of: {choices}'))
    # => Environment variable "NODE_ENV" invalid: ['NODE_ENV must be one of: production, development']

    # multiple validators
    from marshmallow.validate import Length, Email

    env.str('EMAIL', validate=[Length(min=4), Email()])
    # => Environment variable "EMAIL" invalid: ['Shorter than minimum length 4.', 'Not a valid email address.']


Serialization
-------------

.. code-block:: python

    # serialize to a dictionary of simple types (numbers and strings)
    env.dump()
    # {'COORDINATES': [23.3, 50.0],
    # 'ENABLE_FEATURE_X': False,
    # 'ENABLE_LOGIN': True,
    # 'GITHUB_REPOS': ['webargs', 'konch', 'ped'],
    # 'GITHUB_USER': 'sloria',
    # 'MAX_CONNECTIONS': 100,
    # 'MYAPP_HOST': 'lolcathost',
    # 'MYAPP_PORT': 3000,
    # 'SHIP_DATE': '1984-06-25',
    # 'TTL': 42}

Defining custom parser behavior
-------------------------------

.. code-block:: python

    # export DOMAIN='http://myapp.com'
    # export COLOR=invalid

    from furl import furl

    # Register a new parser method for paths
    @env.parser_for('furl')
    def furl_parser(value):
        return furl(value)

    domain = env.furl('DOMAIN')  # => furl('https://myapp.com')


    # Custom parsers can take extra keyword arguments
    @env.parser_for('enum')
    def enum_parser(value, choices):
        if value not in choices:
            raise environs.EnvError('Invalid!')
        return value

    color = env.enum('COLOR', choices=['black'])  # => raises EnvError

Note: Environment variables parsed with a custom parser function will be serialized by ``Env.dump`` without any modification. To define special serialization behavior, use ``Env.parser_from_field`` instead (see next section).

Marshmallow integration
-----------------------

.. code-block:: python

    # export STATIC_PATH='app/static'

    # Custom parsers can be defined as marshmallow Fields
    import pathlib

    import marshmallow as ma

    class PathField(ma.fields.Field):
        def _deserialize(self, value, *args, **kwargs):
            return pathlib.Path(value)

        def _serialize(self, value, *args, **kwargs):
            return str(value)

    env.add_parser_from_field('path', PathField)

    static_path = env.path('STATIC_PATH')  # => PosixPath('app/static')
    env.dump()['STATIC_PATH']  # => 'app/static'

Reading ``.env`` files
----------------------

.. code-block:: bash

    # myapp/.env
    DEBUG=true
    PORT=4567

Call ``Env.read_env`` before parsing variables.

.. code-block:: python

    from environs import Env

    env = Env()
    # Read .env into os.environ
    env.read_env()

    env.bool('DEBUG')  # => True
    env.int('PORT')   # => 4567

Why...?
-------

Why envvars?
++++++++++++

See `The 12-factor App <http://12factor.net/config>`_ section on `configuration <http://12factor.net/config>`_.

Why not ``os.environ``?
+++++++++++++++++++++++

While ``os.environ`` is enough for simple use cases, a typical application will need a way to manipulate and validate raw environment variables. Environs abstracts common tasks for handling environment variables.

Environs will help you

* cast envvars to the correct type
* specify required envvars
* define default values
* validate envvars
* parse list and dict values
* parse dates, datetimes, and timedeltas
* parse proxied variables
* serialize your configuration to JSON, YAML, etc.

Why another library?
++++++++++++++++++++

There are many great Python libraries for parsing environment variables. In fact, most of the credit for environs' public API goes to the authors of `envparse <https://github.com/rconradharris/envparse>`_ and `django-environ <https://github.com/joke2k/django-environ>`_.

environs aims to meet three additional goals:

1. Make it easy to extend parsing behavior and develop plugins.
2. Leverage the deserialization and validation functionality provided by a separate library (marshmallow).
3. Clean up redundant API.


License
-------

MIT licensed. See the `LICENSE <https://github.com/sloria/environs/blob/master/LICENSE>`_ file for more details.

