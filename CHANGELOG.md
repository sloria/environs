# Changelog

### 5.0.0 (2019-07-06)

Features:

- Add `env.path` ([#81](https://github.com/sloria/environs/issues/81)).
  Thanks [umrashrf](https://github.com/umrashrf) for the suggestion.
- Add type annotations.

Other changes:

- _Backwards-incompatible_: Drop support for Python 2. If you use Python 2,
  you will need to use version 4.2.0 or older.

## 4.2.0 (2019-06-01)

- Minor optimization.

Bug fixes:

- Reset prefix when an exception is raised within an `env.prefixed()`
  context ([#78](https://github.com/sloria/environs/issues/78)).
  Thanks [rcuza](https://github.com/rcuza) for the catch and patch.

## 4.1.3 (2019-05-15)

Bug fixes:

- Fix behavior when passing a `dict` value as the default
  to `env.dict` ([#76](https://github.com/sloria/environs/pull/76)).
  Thanks [c-w](https://github.com/c-w) for the PR.

Support:

- Document how to read a specific file with `env.read_env`
  ([#66](https://github.com/sloria/environs/issues/66)).
  Thanks [nvtkaszpir](https://github.com/nvtkaszpir) and
  [c-w](https://github.com/c-w).

## 4.1.2 (2019-05-05)

Bug fixes:

- Fix compatibility with marshmallow 3.0.0>=rc6.

## 4.1.1 (2019-05-04)

Bug fixes:

- Fix accessing proxied envvars when using `env.prefixed`
  ([#72](https://github.com/sloria/environs/issues/72)).
  Thanks [Kamforka](https://github.com/Kamforka) for the catch and patch.
- Fix behavior when an envvar is explicitly set to an empty string
  ([#71](https://github.com/sloria/environs/issues/71)).
  Thanks [twosigmajab](https://github.com/twosigmajab) for reporting
  and thanks [hvtuananh](https://github.com/hvtuananh) for the PR.

## 4.1.0 (2018-12-10)

- `EnvError` subclasses `ValueError` ([#50](https://github.com/sloria/environs/pull/50)).
  Thanks [alexpirine](https://github.com/alexpirine).
- Test against Python 3.7.

## 4.0.0 (2018-08-06)

- Use python-dotenv for parsing .env files. `Env.read_env` behaves
  mostly the same except that a warning isn't raised by default if a
  .env file isn\'t found. Pass `verbose=True` to raise a warning.

## 3.0.0 (2018-08-05)

Features:

- _Backwards-incompatible_: `Env.read_env` raises a warning instead of
  an error when `.env` isn\'t found
  ([#10](https://github.com/sloria/environs/issues/10)). Thanks
  [lachlancooper](https://github.com/lachlancooper) for the
  suggestion.
- Add optional Django support. Install using
  `pip install environs[django]`, which enables `env.dj_db_url` and
  `env.dj_email_url`.

## 2.1.1 (2018-05-21)

Features:

- Fix compatibility with marshmallow 3 beta.

## 2.1.0 (2018-01-25)

Features:

- Add recurse parameter to Env.read_env
  ([#9](https://github.com/sloria/environs/pull/9)). Thanks
  [gthank](https://github.com/gthank) for the PR.

## 2.0.0 (2018-01-02)

Features:

- Add support for nested prefixes
  ([#8](https://github.com/sloria/environs/pull/8)). Thanks
  [gvialetto](https://github.com/gvialetto) for the PR.

Other changes:

- _Backwards-incompatible_: Drop support for Python 3.3 and 3.4.

## 1.2.0 (2017-01-12)

Features:

- Add `url` parser that returns a `urllib.parse.ParseResult`
  ([#6](https://github.com/sloria/environs/issues/6)). Thanks
  [IlyaSemenov](https://github.com/IlyaSemenov) for the suggestion.

Bug fixes:

- Every instance of `Env` gets its own parser map, so calling
  `env.parser_for` for one instance doesn\'t affect other instances.

## 1.1.0 (2016-05-01)

- Add `Env.read_env` method for reading `.env` files.

## 1.0.0 (2016-04-30)

- Support for proxied variables
  ([#2](https://github.com/sloria/environs/issues/2)).
- _Backwards-incompatible_: Remove `env.get` method. Use `env()`
  instead.
- Document how to read `.env` files
  ([#1](https://github.com/sloria/environs/issues/1)).

## 0.1.0 (2016-04-25)

- First PyPI release.
