# Changelog

## 9.3.3 (2021-08-08)

Bug fixes:

- Fix compatibility with marshmallow>=3.13.0 
  so that no DeprecationWarnings are raised ([#224](https://github.com/sloria/environs/issues/224)).

## 9.3.2 (2021-03-28)

Bug fixes:

- Handle JSON decoding errors when using `env.json` ([#212](https://github.com/sloria/environs/pull/212)).
  Thanks [bvanelli](https://github.com/bvanelli) for the PR.

## 9.3.1 (2021-02-07)

Bug fixes:

- Apply variable expansion to default values ([#204](https://github.com/sloria/environs/pull/204)).
  Thanks [rjcohn](https://github.com/rjcohn) for the PR.

## 9.3.0 (2020-12-26)

Deprecations:

- Rename `subcast_key` argument of `env.dict` to `subcast_keys`
  for consistency with `subcast_values`. `subcast_key` is deprecated.

## 9.2.0 (2020-11-07)

Features:

- Add time parser ([#191](https://github.com/sloria/environs/issues/191)).

## 9.1.0 (2020-11-06)

Features:

- Add `enum` parser ([#185](https://github.com/sloria/environs/pull/185)).
- Add `delimiter` param to `env.list`
  ([#184](https://github.com/sloria/environs/pull/184)).

Thanks [tomgrin10](https://github.com/tomgrin10) for the PRs.

Bug fixes:

- Loosen `ParserMethod` typing ([#186 (comment)](https://github.com/sloria/environs/issues/186#issuecomment-723163520)).
  Thanks [hukkinj1](https://github.com/hukkinj1) for the PR.

Other changes:

- When using deferred validation (`eager=False`), parser methods return `None`
  for missing or invalid values.
  _Note_: This may break code that depended on parser methods returning `marshmallow.missing`,
  but this behavior was not documented nor tested and therefore is not considered public API.

## 9.0.0 (2020-10-31)

- _Backwards-incompatible_: Rename `subcast` param of `env.dict` to `subcast_values` for consistency with `subcast_keys`.
- _Backwards-incompatible_: Remove variable proxying. Use variable expansion instead (see 8.1.0 release notes below)
  ([#175](https://github.com/sloria/environs/issues/175)).
- _Backwards-incompatible_: Drop support for marshmallow 2 and Python 3.5,
  which are both EOL ([#174](https://github.com/sloria/environs/issues/174)).

## 8.1.0 (2020-10-31)

Features:

- Add support for variable expansion, e.g. `MY_VAR=${MY_OTHER_VAR:-mydefault}` ([#164](https://github.com/sloria/environs/issues/164)).
  Thanks [gnarvaja](https://github.com/gnarvaja) for the PR.

Deprecations:

- Variable proxying using the `{{VAR}}` syntax is deprecated
  and will be removed in environs 9.0.0.
  Use variable expansion using `${VAR}` instead.

```bash
# Before
export MAILGUN_LOGIN=sloria
export SMTP_LOGIN={{MAILGUN_LOGIN}}

# After
export MAILGUN_LOGIN=sloria
export SMTP_LOGIN=${MAILGUN_LOGIN}
```

```python
from environs import Env

env = Env(expand_vars=True)

SMTP_LOGIN = env.str("SMTP_LOGIN")  # => 'sloria'
```

Bug fixes:

- Fix deferred validation behavior for `dj_db_url`, `dj_email_url`, `dj_cache_url`,
  and custom parsers ([#121](https://github.com/sloria/environs/issues/121)).
  Thanks [hukkinj1](https://github.com/hukkinj1) for reporting.

Other changes:

- Test against Python 3.9.
- Remove usage of implicit `typing.Optional` ([171](https://github.com/sloria/environs/issues/171)).

## 8.0.0 (2020-05-27)

Bug fixes:

- Fix behavior of recurse=True when custom filepath is passed to `env.read_env`
  ([#100](https://github.com/sloria/environs/issues/100)). Thanks [ribeaud](https://github.com/ribeaud) and [timoklimmer](https://github.com/sloria/environs/pull/157) for the help.

Other changes:

- _Backwards-incompatible_: As a result of the above fix, passing a directory to `env.read_env` is no longer allowed and will raise a `ValueError`.
  Only file paths or file names should be passed.

## 7.4.0 (2020-04-18)

- Add `subcast_key` argument to `env.dict` ([#151](https://github.com/sloria/environs/issues/151)).
  Thanks [AugPro](https://github.com/AugPro) for the suggestion and PR.

## 7.3.1 (2020-03-22)

- Fix error when parsing empty list with subcast
  [#137](https://github.com/sloria/environs/issues/137).
  Thanks [sabdouni] for the catch and patch.

## 7.3.0 (2020-03-01)

- `log_level` accepts lower-cased log level names and rejects invalid
  names ([#138](https://github.com/sloria/environs/pull/138)).
  Thanks [gnarvaja](https://github.com/gnarvaja) for the PR.

## 7.2.0 (2020-02-09)

- Add `dj_cache_url` for caching Django cache URLs (requires installing with `[django]`)
  ([#126](https://github.com/sloria/environs/issues/126)).
  Thanks [epicserve](https://github.com/epicserve) for the suggestion and PR.

## 7.1.0 (2019-12-07)

- Improve typings and run mypy with dependencies type annotations ([#115](https://github.com/sloria/environs/pull/115)).
- Distribute types per PEP 561 ([#116](https://github.com/sloria/environs/pull/116)).

Thanks [hukkinj1](https://github.com/hukkinj1) for the PRs.

## 7.0.0 (2019-12-02)

- _Backwards-incompatible_: Remove `stream` argument from `read_env`,
  since it had no effect ([#114](https://github.com/sloria/environs/pull/114)).
- _Backwards-incompatible_: `Env.read_env` consistently returns `None`
  ([#111](https://github.com/sloria/environs/pull/111)).
- Remove unnecessary `__str__` definition ([#112](https://github.com/sloria/environs/pull/112)).

Thanks [hukkinj1](https://github.com/hukkinj1) for the PRs.

## 6.1.0 (2019-11-03)

Features:

- Add deferred validation via the `eager` parameter and `env.seal()` ([#56](https://github.com/sloria/environs/issues/56)).
  Thanks [robertlagrant](https://github.com/robertlagrant) for the suggestion.

Other changes:

- Test against Python 3.8 ([#108](https://github.com/sloria/environs/pull/108)).

## 6.0.0 (2019-09-22)

Features:

- Default parser methods are now defined as bound methods.
  This enables static analysis features, e.g. autocomplete ([#103](https://github.com/sloria/environs/issues/103)).
  Thanks [rugleb](https://github.com/rugleb) for the suggestion.
  _Backwards-incompatible_: As a result of this change, adding a parser name that is the same as an existing method
  will result in an error being raised.

```python
import environs

env = environs.Env()

# Below conflicts with built-in `url` method.
# In <6.0.0, this would override the built-in method.
# In >=6.0.0, this raises an error:
#   environs.ParserConflictError: Env already has a method with name 'url'. Use a different name.
@env.parser_for("url")
def https_url(value):
    return "https://" + value
```

Bug fixes:

- Fix error message for prefixed variables ([#102](https://github.com/sloria/environs/issues/102)).
  Thanks [AGeekInside](https://github.com/AGeekInside) for reporting.

Other changes:

- _Backwards-incompatible_: Rename `Env.__parser_map__` to `Env.__custom_parsers__`.

## 5.2.1 (2019-08-08)

Bug fixes:

- Fix behavior when recursively searching for a specified file
  ([#96](https://github.com/sloria/environs/issues/96)).
  Thanks [ribeaud](https://github.com/ribeaud) for the catch and patch.

## 5.2.0 (2019-07-19)

Changes:

- Improve typings.

## 5.1.0 (2019-07-13)

Features:

- Add `env.log_level` ([#7](https://github.com/sloria/environs/issues/7)).
- Use `raise from` to improve tracebacks.

Other changes:

- Improve typings.

## 5.0.0 (2019-07-06)

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
