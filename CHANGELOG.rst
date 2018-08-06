*********
Changelog
*********

4.0.0 (unreleased)
------------------

* Use python-dotenv for parsing .env files. ``Env.read_env`` behaves mostly the
  same except that a warning isn't raised by default if a .env file
  isn't found. Pass ``verbose=True`` to raise a warning.

3.0.0 (2018-08-05)
------------------

Features:

* *Backwards-incompatible*: ``Env.read_env`` raises a warning instead of an error when ``.env``
  isn't found (`#10 <https://github.com/sloria/environs/issues/10>`_).
  Thanks `lachlancooper <https://github.com/lachlancooper>`_ for the
  suggestion.
* Add optional Django support. Install using ``pip install environs[django]``, which
  enables ``env.dj_db_url`` and ``env.dj_email_url``.

2.1.1 (2018-05-21)
------------------

Features:

* Fix compatibility with marshmallow 3 beta.

2.1.0 (2018-01-25)
------------------

Features:

* Add `recurse` parameter to `Env.read_env` (`#9 <https://github.com/sloria/environs/pull/9>`_).
  Thanks `gthank <https://github.com/gthank>`_ for the PR.

2.0.0 (2018-01-02)
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
