*********
Changelog
*********

1.2.0 (2017-01-12)
------------------

Features:

* Add ``url`` parser that returns a ``urllib.parse.ParseResult`` (`#6 <https://github.com/sloria/environs/issues/6>`_). Thanks `IlyaSemenov <https://github.com/IlyaSemenov>`_ for the suggestion.

Bug fixes:

* Every instance of ``Env`` gets its own parser map, so calling ``env.parser_for`` for one instance doesn't affect other instances.

1.1.0 (2016-05-01)
------------------

* Add ``Env.read_env`` method for reading ``.env`` files.

1.0.0 (2016-04-30)
------------------

* Support for proxied variables (`#2 <https://github.com/sloria/environs/issues/2>`_).
* *Backwards-incompatible*: Remove ``env.get`` method. Use ``env()`` instead.
* Document how to read ``.env`` files (`#1 <https://github.com/sloria/environs/issues/1>`_).

0.1.0 (2016-04-25)
------------------

* First PyPI release.
