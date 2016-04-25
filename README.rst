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

Envargs is inspired by `envparse <https://github.com/rconradharris/envparse>`_ and uses `marshmallow <https://github.com/marshmallow-code/marshmallow>`_ under the hood for deserializing and serializing values.

Basic usage
===========

.. code-block:: python

    # export GITHUB_USER=sloria
    # export API_KEY=123abc
    # export SHIP_DATE='1984-06-25'
    # export ENABLE_LOGIN=true
    # export MAX_CONNECTIONS=42
    # export GITHUB_REPOS=webargs,konch,ped
    # export COORDINATES=23.3,50.0

    from envargs import Env

    env = Env()
    # reading an environment variable
    gh_user = env('GITHUB_USER')  # => 'sloria'
    # casting
    api_key = env.str('API_KEY')  # => '123abc'
    date = env.date('SHIP_DATE')  # => datetime.date(1984, 6, 25)
    # providing a default value
    enable_login = env.bool('ENABLE_LOGIN', False)  # => True
    enable_feature_x = env.bool('ENABLE_FEATURE_X', False)  # => False
    # parsing lists
    gh_repos = env.list('GITHUB_REPOS')  # => ['webargs', 'konch', 'ped']
    coords = env.list('COORDINATES', subcast=float)  # => [23.3, 50.0]


Handling prefixes
=================

.. code-block:: python

    # export MYAPP_HOST=lolcathost
    # export MYAPP_PORT=3000

    with env.prefixed('MYAPP_'):
        host = env('HOST', 'localhost')  # => 'lolcathost'
        port = env.int('PORT', 5000)  # => 3000

Serialization
=============

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
===============================

.. code-block:: python

    # export DOMAIN='http://myapp.com'
    from furl import furl

    # Register a new parser method for paths
    @env.parser_for('furl')
    def furl_parser(value):
        return furl(value)

    domain = env.furl('DOMAIN')  # => furl('https://myapp.com')

Note: Environment variables parsed with a custom parser function will be serialized by ``Env.dump`` without any modification. To define special serialization behavior, use ``Env.parser_from_field`` instead (see next section).


Marshmallow integration
=======================

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

    env.parser_from_field('path', PathField)

    static_path = env.path('STATIC_PATH')  # => PosixPath('app/static')
    env.dump()['STATIC_PATH']  # => 'app/static'

License
=======

MIT licensed. See the `LICENSE <https://github.com/sloria/envargs/blob/dev/LICENSE>`_ file for more details.
