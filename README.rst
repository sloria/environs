************************************************
envargs: simplified environment variable parsing
************************************************

.. .. image:: https://badge.fury.io/py/envargs.png
..     :target: http://badge.fury.io/py/envargs
..     :alt: Latest version
..

.. image:: https://travis-ci.org/sloria/envargs.svg?branch=master
    :target: https://travis-ci.org/sloria/envargs
    :alt: Travis-CI


Envargs is a Python library for parsing environment variables.

Envargs is inspired by `envparse <https://github.com/rconradharris/envparse>`_ and uses `marshmallow <https://github.com/marshmallow-code/marshmallow>`_ under the hood for validating, deserializing, and serializing values.

.. Get it now
.. ----------
.. ::
..
..     pip install envargs

Basic usage
-----------

.. code-block:: python

    # export GITHUB_USER=sloria
    # export API_KEY=123abc
    # export SHIP_DATE='1984-06-25'
    # export ENABLE_LOGIN=true
    # export GITHUB_REPOS=webargs,konch,ped
    # export COORDINATES=23.3,50.0

    from envargs import Env

    env = Env()
    # reading an environment variable
    gh_user = env('GITHUB_USER')  # => 'sloria'
    secret = env('SECRET')  # => raises error if not set

    # casting
    api_key = env.str('API_KEY')  # => '123abc'
    date = env.date('SHIP_DATE')  # => datetime.date(1984, 6, 25)

    # providing a default value
    enable_login = env.bool('ENABLE_LOGIN', False)  # => True
    enable_feature_x = env.bool('ENABLE_FEATURE_X', False)  # => False

    # parsing lists
    gh_repos = env.list('GITHUB_REPOS')  # => ['webargs', 'konch', 'ped']
    coords = env.list('COORDINATES', subcast=float)  # => [23.3, 50.0]


Supported types
---------------

The following are all type-casting methods of  ``Env``:

* ``str``
* ``bool``
* ``int``
* ``float``
* ``decimal``
* ``list`` (accepts optional ``subcast`` keyword argument)
* ``dict`` (accepts optional ``subcast`` keyword argument)
* ``json``
* ``datetime``
* ``date``
* ``timedelta`` (assumes value is an integer in seconds)
* ``uuid``


Handling prefixes
-----------------

.. code-block:: python

    # export MYAPP_HOST=lolcathost
    # export MYAPP_PORT=3000

    with env.prefixed('MYAPP_'):
        host = env('HOST', 'localhost')  # => 'lolcathost'
        port = env.int('PORT', 5000)  # => 3000


Validation
----------

.. code-block:: python

    # export TTL=-2
    # export NODE_ENV='invalid'
    # export EMAIL='^_^'


    # simple validator
    env.int('TTL', validate=lambda n: n > 0)  # => 'sloria'
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
    # { 'API_KEY': '123abc',
    # 'COORDINATES': [23.3, 50.0],
    # 'ENABLE_FEATURE_X': False,
    # 'ENABLE_LOGIN': True,
    # 'GITHUB_REPOS': ['webargs', 'konch', 'ped'],
    # 'GITHUB_USER': 'sloria',
    # 'MYAPP_HOST': 'lolcathost',
    # 'MYAPP_PORT': 3000,
    # 'SHIP_DATE': '1984-06-25'}

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
            raise envargs.EnvError('Invalid!')
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

License
-------

MIT licensed. See the `LICENSE <https://github.com/sloria/envargs/blob/dev/LICENSE>`_ file for more details.
