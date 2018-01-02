*********
Changelog
*********

2.0.0 (unreleased)
------------------

Features:

* Add support for nested prefixes (`#8 <https://github.com/sloria/environs/pull/8>`_).
  Thanks `gvialetto <https://github.com/gvialetto>`_ for the PR.

Other changes:

* *Backwards-incompatible*: Drop support for Python 3.3 and 3.4.

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
