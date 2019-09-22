import contextlib
import inspect
import functools
import json as pyjson
import logging
import os
import re
import typing
from collections.abc import Mapping
from urllib.parse import urlparse, ParseResult
from pathlib import Path

import marshmallow as ma
from dotenv.main import load_dotenv, DotEnv, _walk_to_root

__version__ = "6.0.0"
__all__ = ["EnvError", "Env"]

MARSHMALLOW_VERSION_INFO = tuple([int(part) for part in ma.__version__.split(".") if part.isdigit()])
_PROXIED_PATTERN = re.compile(r"\s*{{\s*(\S*)\s*}}\s*")

_T = typing.TypeVar("_T")
_StrType = str
_BoolType = bool
_IntType = int

FieldFactory = typing.Callable[..., ma.fields.Field]
Subcast = typing.Union[typing.Type, typing.Callable[..., _T]]
FieldType = typing.Type[ma.fields.Field]
FieldOrFactory = typing.Union[FieldType, FieldFactory]
ParserMethod = typing.Callable[..., _T]


class EnvError(ValueError):
    """Raised when an environment variable or if a required environment variable is unset."""


class ParserConflictError(ValueError):
    """Raised when adding a custom parser that conflicts with a built-in parser method."""


def _field2method(
    field_or_factory: FieldOrFactory, method_name: str, *, preprocess: typing.Callable = None
) -> ParserMethod:
    def method(
        self: "Env", name: str, default: typing.Any = ma.missing, subcast: Subcast = None, **kwargs
    ) -> _T:
        missing = kwargs.pop("missing", None) or default
        if isinstance(field_or_factory, type) and issubclass(field_or_factory, ma.fields.Field):
            field = typing.cast(typing.Type[ma.fields.Field], field_or_factory)(missing=missing, **kwargs)
        else:
            field = typing.cast(FieldFactory, field_or_factory)(subcast=subcast, missing=missing, **kwargs)
        parsed_key, raw_value, proxied_key = self._get_from_environ(name, ma.missing)
        self._fields[parsed_key] = field
        source_key = proxied_key or parsed_key
        if raw_value is ma.missing and field.missing is ma.missing:
            raise EnvError('Environment variable "{}" not set'.format(source_key))
        if raw_value or raw_value == "":
            value = raw_value
        else:
            value = field.missing
        if preprocess:
            value = preprocess(value, subcast=subcast, **kwargs)
        try:
            value = field.deserialize(value)
        except ma.ValidationError as error:
            raise EnvError(
                'Environment variable "{}" invalid: {}'.format(source_key, error.args[0])
            ) from error
        else:
            self._values[parsed_key] = value
            return value

    method.__name__ = method_name
    return method


def _func2method(func: typing.Callable, method_name: str) -> ParserMethod:
    def method(
        self: "Env", name: str, default: typing.Any = ma.missing, subcast: typing.Type = None, **kwargs
    ):
        parsed_key, raw_value, proxied_key = self._get_from_environ(name, default)
        if raw_value is ma.missing:
            raise EnvError('Environment variable "{}" not set'.format(proxied_key or parsed_key))
        value = func(raw_value, **kwargs)
        self._fields[parsed_key] = ma.fields.Field(**kwargs)
        self._values[parsed_key] = value
        return value

    method.__name__ = method_name
    return method


# From webargs
def _dict2schema(dct, schema_class=ma.Schema):
    """Generate a `marshmallow.Schema` class given a dictionary of
    `Fields <marshmallow.fields.Field>`.
    """
    if hasattr(schema_class, "from_dict"):  # marshmallow 3
        return schema_class.from_dict(dct)
    attrs = dct.copy()

    class Meta:
        strict = True

    attrs["Meta"] = Meta
    return type("", (schema_class,), attrs)


def _make_list_field(*, subcast: Subcast, **kwargs) -> ma.fields.List:
    inner_field = ma.Schema.TYPE_MAPPING[subcast] if subcast else ma.fields.Field
    return ma.fields.List(inner_field, **kwargs)


def _preprocess_list(value: typing.Union[str, typing.Iterable], **kwargs) -> typing.Iterable:
    return value if ma.utils.is_iterable_but_not_string(value) else typing.cast(str, value).split(",")


def _preprocess_dict(
    value: typing.Union[str, typing.Mapping[str, _T]], subcast: Subcast, **kwargs
) -> typing.Mapping[str, _T]:
    if isinstance(value, Mapping):
        return value

    return {
        key.strip(): subcast(val.strip()) if subcast else val.strip()
        for key, val in (item.split("=") for item in value.split(",") if value)
    }


def _preprocess_json(value: str, **kwargs):
    return pyjson.loads(value)


def _dj_db_url_parser(value: str, **kwargs) -> dict:
    try:
        import dj_database_url
    except ImportError as error:
        raise RuntimeError(
            "The dj_db_url parser requires the dj-database-url package. "
            "You can install it with: pip install dj-database-url"
        ) from error
    return dj_database_url.parse(value, **kwargs)


def _dj_email_url_parser(value: str, **kwargs) -> dict:
    try:
        import dj_email_url
    except ImportError as error:
        raise RuntimeError(
            "The dj_email_url parser requires the dj-email-url package. "
            "You can install it with: pip install dj-email-url"
        ) from error
    return dj_email_url.parse(value, **kwargs)


class URLField(ma.fields.URL):
    def _serialize(self, value: ParseResult, *args, **kwargs) -> str:
        return value.geturl()

    # Override deserialize rather than _deserialize because we need
    # to call urlparse *after* validation has occurred
    def deserialize(self, value: str, attr: str = None, data: typing.Mapping = None) -> ParseResult:
        ret = super().deserialize(value, attr, data)
        return urlparse(ret)


class PathField(ma.fields.Str):
    def _deserialize(self, value, *args, **kwargs) -> Path:
        ret = super()._deserialize(value, *args, **kwargs)
        return Path(ret)


class LogLevelField(ma.fields.Int):
    def _format_num(self, value) -> int:
        try:
            return super()._format_num(value)
        except (TypeError, ValueError) as error:
            if hasattr(logging, value):
                return getattr(logging, value)
            else:
                raise ma.ValidationError("Not a valid log level.") from error


class Env:
    """An environment variable reader."""

    __call__ = _field2method(ma.fields.Field, "__call__")  # type: ParserMethod

    int = _field2method(ma.fields.Int, "int")
    bool = _field2method(ma.fields.Bool, "bool")
    str = _field2method(ma.fields.Str, "str")
    float = _field2method(ma.fields.Float, "float")
    decimal = _field2method(ma.fields.Decimal, "decimal")
    list = _field2method(_make_list_field, "list", preprocess=_preprocess_list)
    dict = _field2method(ma.fields.Dict, "dict", preprocess=_preprocess_dict)
    json = _field2method(ma.fields.Field, "json", preprocess=_preprocess_json)
    datetime = _field2method(ma.fields.DateTime, "datetime")
    date = _field2method(ma.fields.Date, "date")
    path = _field2method(PathField, "path")
    log_level = _field2method(LogLevelField, "log_level")
    timedelta = _field2method(ma.fields.TimeDelta, "timedelta")
    uuid = _field2method(ma.fields.UUID, "uuid")
    url = _field2method(URLField, "url")
    dj_db_url = _func2method(_dj_db_url_parser, "dj_db_url")
    dj_email_url = _func2method(_dj_email_url_parser, "dj_email_url")

    def __init__(self):
        self._fields = {}  # type: typing.Dict[_StrType, ma.fields.Field]
        self._values = {}  # type: typing.Dict[_StrType, typing.Any]
        self._prefix = None  # type: typing.Optional[_StrType]
        self.__custom_parsers__ = {}

    def __repr__(self) -> _StrType:
        return "<{} {}>".format(self.__class__.__name__, self._values)

    __str__ = __repr__

    @staticmethod
    def read_env(
        path: _StrType = None,
        recurse: _BoolType = True,
        stream: _StrType = None,
        verbose: _BoolType = False,
        override: _BoolType = False,
    ) -> DotEnv:
        """Read a .env file into os.environ.

        If .env is not found in the directory from which this method is called,
        the default behavior is to recurse up the directory tree until a .env
        file is found. If you do not wish to recurse up the tree, you may pass
        False as a second positional argument.
        """
        # By default, start search from the same file this function is called
        if path is None:
            current_frame = inspect.currentframe()
            if not current_frame:
                raise RuntimeError("Could not get current call frame.")
            frame = current_frame.f_back
            caller_dir = os.path.dirname(frame.f_code.co_filename)
            # Will be a directory
            start = os.path.join(os.path.abspath(caller_dir))
        else:
            # Could be directory or a file
            start = path
        if recurse:
            env_name = os.path.basename(start) if os.path.isfile(start) else ".env"
            for dirname in _walk_to_root(start):
                check_path = os.path.join(dirname, env_name)
                if os.path.exists(check_path):
                    return load_dotenv(check_path, stream=stream, verbose=verbose, override=override)
        else:
            if path is None:
                start = os.path.join(start, ".env")
            return load_dotenv(start, stream=stream, verbose=verbose, override=override)

    @contextlib.contextmanager
    def prefixed(self, prefix: _StrType) -> typing.Iterator["Env"]:
        """Context manager for parsing envvars with a common prefix."""
        try:
            old_prefix = self._prefix
            if old_prefix is None:
                self._prefix = prefix
            else:
                self._prefix = "{}{}".format(old_prefix, prefix)
            yield self
        finally:
            # explicitly reset the stored prefix on completion and exceptions
            self._prefix = None
        self._prefix = old_prefix

    def __getattr__(self, name: _StrType, **kwargs):
        try:
            return functools.partial(self.__custom_parsers__[name], self)
        except KeyError as error:
            raise AttributeError("{} has no attribute {}".format(self, name)) from error

    def add_parser(self, name: _StrType, func: typing.Callable) -> None:
        """Register a new parser method with the name ``name``. ``func`` must
        receive the input value for an environment variable.
        """
        if hasattr(self, name):
            raise ParserConflictError(
                "Env already has a method with name '{}'. Use a different name.".format(name)
            )
        self.__custom_parsers__[name] = _func2method(func, method_name=name)
        return None

    def parser_for(self, name: _StrType) -> typing.Callable[[typing.Callable], typing.Callable]:
        """Decorator that registers a new parser method with the name ``name``.
        The decorated function must receive the input value for an environment variable.
        """

        def decorator(func: typing.Callable) -> typing.Callable:
            self.add_parser(name, func)
            return func

        return decorator

    def add_parser_from_field(self, name: _StrType, field_cls: typing.Type[ma.fields.Field]):
        """Register a new parser method with name ``name``, given a marshmallow ``Field``."""
        self.__custom_parsers__[name] = _field2method(field_cls, method_name=name)

    def dump(self) -> typing.Mapping[_StrType, typing.Any]:
        """Dump parsed environment variables to a dictionary of simple data types (numbers
        and strings).
        """
        schema = _dict2schema(self._fields)()
        dump_result = schema.dump(self._values)
        return dump_result.data if MARSHMALLOW_VERSION_INFO[0] < 3 else dump_result

    def _get_from_environ(
        self, key: _StrType, default: typing.Any, *, proxied: _BoolType = False
    ) -> typing.Tuple[_StrType, typing.Any, typing.Optional[_StrType]]:
        """Access a value from os.environ. Handles proxied variables, e.g. SMTP_LOGIN={{MAILGUN_LOGIN}}.

        Returns a tuple (envvar_key, envvar_value, proxied_key). The ``envvar_key`` will be different from
        the passed key for proxied variables. proxied_key will be None if the envvar isn't proxied.

        The ``proxied`` flag is recursively passed if a proxy lookup is required to get a
        proxy env key.
        """
        env_key = self._get_key(key, omit_prefix=proxied)
        value = os.environ.get(env_key, default)
        if hasattr(value, "strip"):
            match = _PROXIED_PATTERN.match(value)
            if match:  # Proxied variable
                proxied_key = match.groups()[0]
                return (key, self._get_from_environ(proxied_key, default, proxied=True)[1], proxied_key)
        return env_key, value, None

    def _get_key(self, key: _StrType, *, omit_prefix: _BoolType = False) -> _StrType:
        return self._prefix + key if self._prefix and not omit_prefix else key
