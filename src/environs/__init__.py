import collections
import contextlib
import functools
import inspect
import json as pyjson
import logging
import os
import re
import typing
from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from urllib.parse import ParseResult, urlparse

import marshmallow as ma
from dotenv.main import _walk_to_root, load_dotenv

__all__ = ["EnvError", "Env"]

_T = typing.TypeVar("_T")
_StrType = str
_BoolType = bool

ErrorMapping = typing.Mapping[str, typing.List[str]]
ErrorList = typing.List[str]
FieldFactory = typing.Callable[..., ma.fields.Field]
Subcast = typing.Union[typing.Type, typing.Callable[..., _T], ma.fields.Field]
FieldType = typing.Type[ma.fields.Field]
FieldOrFactory = typing.Union[FieldType, FieldFactory]
ParserMethod = typing.Callable


_EXPANDED_VAR_PATTERN = re.compile(r"(?<!\\)\$\{([A-Za-z0-9_]+)(:-[^\}:]*)?\}")


class EnvError(ValueError):
    """Raised when an environment variable or
    if a required environment variable is unset.
    """


class EnvValidationError(EnvError):
    def __init__(
        self, message: str, error_messages: typing.Union[ErrorList, ErrorMapping]
    ):
        self.error_messages = error_messages
        super().__init__(message)


class EnvSealedError(TypeError, EnvError):
    pass


class ParserConflictError(ValueError):
    """Raised when adding a custom parser that conflicts
    with a built-in parser method.
    """


def _field2method(
    field_or_factory: FieldOrFactory,
    method_name: str,
    *,
    preprocess: typing.Optional[typing.Callable] = None,
    preprocess_kwarg_names: typing.Sequence[str] = tuple(),
) -> ParserMethod:
    def method(
        self: "Env",
        name: str,
        default: typing.Any = ma.missing,
        subcast: typing.Optional[Subcast] = None,
        *,
        # Subset of relevant marshmallow.Field kwargs
        load_default: typing.Any = ma.missing,
        validate: typing.Optional[
            typing.Union[
                typing.Callable[[typing.Any], typing.Any],
                typing.Iterable[typing.Callable[[typing.Any], typing.Any]],
            ]
        ] = None,
        required: bool = False,
        allow_none: typing.Optional[bool] = None,
        error_messages: typing.Optional[typing.Dict[str, str]] = None,
        metadata: typing.Optional[typing.Mapping[str, typing.Any]] = None,
        **kwargs,
    ) -> typing.Optional[_T]:
        if self._sealed:
            raise EnvSealedError(
                "Env has already been sealed. New values cannot be parsed."
            )
        field_kwargs = dict(
            validate=validate,
            required=required,
            allow_none=allow_none,
            load_default=load_default or default,
            error_messages=error_messages,
            metadata=metadata,
        )
        preprocess_kwargs = {
            name: kwargs.pop(name) for name in preprocess_kwarg_names if name in kwargs
        }
        if isinstance(field_or_factory, type) and issubclass(
            field_or_factory, ma.fields.Field
        ):
            field = field_or_factory(**field_kwargs, **kwargs)
        else:
            parsed_subcast = _make_subcast_field(subcast)
            field = field_or_factory(subcast=parsed_subcast, **field_kwargs)
        parsed_key, value, proxied_key = self._get_from_environ(
            name, field.load_default
        )
        self._fields[parsed_key] = field
        source_key = proxied_key or parsed_key
        if value is ma.missing:
            if self.eager:
                raise EnvError(
                    f'Environment variable "{proxied_key or parsed_key}" not set'
                )
            else:
                self._errors[parsed_key].append("Environment variable not set.")
                return None
        try:
            if preprocess:
                value = preprocess(value, **preprocess_kwargs)
            value = field.deserialize(value)
        except ma.ValidationError as error:
            if self.eager:
                raise EnvValidationError(
                    f'Environment variable "{source_key}" invalid: {error.args[0]}',
                    error.messages,
                ) from error
            self._errors[parsed_key].extend(error.messages)
        else:
            self._values[parsed_key] = value
        return value

    method.__name__ = method_name
    return method


def _func2method(func: typing.Callable, method_name: str) -> ParserMethod:
    def method(
        self: "Env",
        name: str,
        default: typing.Any = ma.missing,
        **kwargs,
    ) -> typing.Optional[_T]:
        if self._sealed:
            raise EnvSealedError(
                "Env has already been sealed. New values cannot be parsed."
            )
        parsed_key, raw_value, proxied_key = self._get_from_environ(name, default)
        self._fields[parsed_key] = ma.fields.Field()
        source_key = proxied_key or parsed_key
        if raw_value is ma.missing:
            if self.eager:
                raise EnvError(
                    f'Environment variable "{proxied_key or parsed_key}" not set'
                )
            else:
                self._errors[parsed_key].append("Environment variable not set.")
                return None
        if raw_value or raw_value == "":
            value = raw_value
        else:
            value = None
        try:
            value = func(raw_value, **kwargs)
        except (EnvError, ma.ValidationError) as error:
            messages = (
                error.messages
                if isinstance(error, ma.ValidationError)
                else [error.args[0]]
            )
            if self.eager:
                raise EnvValidationError(
                    f'Environment variable "{source_key}" invalid: {error.args[0]}',
                    messages,
                ) from error
            self._errors[parsed_key].extend(messages)
        else:
            self._values[parsed_key] = value
        return value

    method.__name__ = method_name
    return method


def _make_subcast_field(
    subcast: typing.Optional[Subcast],
) -> typing.Type[ma.fields.Field]:
    if isinstance(subcast, type) and subcast in ma.Schema.TYPE_MAPPING:
        inner_field = ma.Schema.TYPE_MAPPING[subcast]
    elif isinstance(subcast, type) and issubclass(subcast, ma.fields.Field):
        inner_field = subcast
    elif callable(subcast):

        class SubcastField(ma.fields.Field):
            def _deserialize(self, value, *args, **kwargs):
                func = typing.cast(typing.Callable[..., _T], subcast)
                return func(value)

        inner_field = SubcastField
    else:
        inner_field = ma.fields.Field
    return inner_field


def _make_list_field(*, subcast: typing.Optional[type], **kwargs) -> ma.fields.List:
    inner_field = _make_subcast_field(subcast)
    return ma.fields.List(inner_field, **kwargs)


def _preprocess_list(
    value: typing.Union[str, typing.Iterable], *, delimiter: str = ",", **kwargs
) -> typing.Iterable:
    if ma.utils.is_iterable_but_not_string(value) or value is None:
        return value
    return typing.cast(str, value).split(delimiter) if value != "" else []


def _preprocess_dict(
    value: typing.Union[str, typing.Mapping],
    *,
    subcast_keys: typing.Optional[Subcast] = None,
    subcast_values: typing.Optional[Subcast] = None,
    delimiter: str = ",",
    **kwargs,
) -> typing.Mapping:
    if isinstance(value, Mapping):
        return value
    subcast_keys_instance: ma.fields.Field = _make_subcast_field(subcast_keys)(**kwargs)
    subcast_values_instance: ma.fields.Field = _make_subcast_field(subcast_values)(
        **kwargs
    )

    return {
        subcast_keys_instance.deserialize(
            key.strip()
        ): subcast_values_instance.deserialize(val.strip())
        for key, val in (item.split("=", 1) for item in value.split(delimiter) if value)
    }


def _preprocess_json(value: typing.Union[str, typing.Mapping, typing.List], **kwargs):
    try:
        if isinstance(value, str):
            return pyjson.loads(value)
        elif isinstance(value, dict) or isinstance(value, list) or value is None:
            return value
        else:
            raise ma.ValidationError("Not valid JSON.")
    except pyjson.JSONDecodeError as error:
        raise ma.ValidationError("Not valid JSON.") from error


_EnumT = typing.TypeVar("_EnumT", bound=Enum)


def _enum_parser(value, type: typing.Type[_EnumT], ignore_case: bool = False) -> _EnumT:
    invalid_exc = ma.ValidationError(f"Not a valid '{type.__name__}' enum.")

    if not ignore_case:
        try:
            return type[value]
        except KeyError as error:
            raise invalid_exc from error

    for enum_value in type:
        if enum_value.name.lower() == value.lower():
            return enum_value

    raise invalid_exc


def _dj_db_url_parser(value: str, **kwargs) -> dict:
    try:
        import dj_database_url
    except ImportError as error:
        raise RuntimeError(
            "The dj_db_url parser requires the dj-database-url package. "
            "You can install it with: pip install dj-database-url"
        ) from error
    try:
        return dj_database_url.parse(value, **kwargs)
    except Exception as error:
        raise ma.ValidationError("Not a valid database URL.") from error


def _dj_email_url_parser(value: str, **kwargs) -> dict:
    try:
        import dj_email_url
    except ImportError as error:
        raise RuntimeError(
            "The dj_email_url parser requires the dj-email-url package. "
            "You can install it with: pip install dj-email-url"
        ) from error
    try:
        return dj_email_url.parse(value, **kwargs)
    except Exception as error:
        raise ma.ValidationError("Not a valid email URL.") from error


def _dj_cache_url_parser(value: str, **kwargs) -> dict:
    try:
        import django_cache_url
    except ImportError as error:
        raise RuntimeError(
            "The dj_cache_url parser requires the django-cache-url package. "
            "You can install it with: pip install django-cache-url"
        ) from error
    try:
        return django_cache_url.parse(value, **kwargs)
    except Exception as error:
        # django_cache_url may raise Exception("Unknown backend...")
        #   so use that error message in the validation error
        raise ma.ValidationError(error.args[0]) from error


class URLField(ma.fields.URL):
    def _serialize(self, value: ParseResult, *args, **kwargs) -> str:
        return value.geturl()

    # Override deserialize rather than _deserialize because we need
    # to call urlparse *after* validation has occurred
    def deserialize(
        self,
        value: str,
        attr: typing.Optional[str] = None,
        data: typing.Optional[typing.Mapping] = None,
        **kwargs,
    ) -> ParseResult:
        ret = super().deserialize(value, attr, data, **kwargs)
        return urlparse(ret)


class PathField(ma.fields.Str):
    def _deserialize(self, value, *args, **kwargs) -> Path:
        if isinstance(value, Path):
            return value
        ret = super()._deserialize(value, *args, **kwargs)
        return Path(ret)


class LogLevelField(ma.fields.Int):
    def _format_num(self, value) -> int:
        try:
            return super()._format_num(value)
        except (TypeError, ValueError) as error:
            value = value.upper()
            if hasattr(logging, value) and isinstance(getattr(logging, value), int):
                return getattr(logging, value)
            else:
                raise ma.ValidationError("Not a valid log level.") from error


class Env:
    """An environment variable reader."""

    __call__: ParserMethod = _field2method(ma.fields.Field, "__call__")

    int = _field2method(ma.fields.Int, "int")
    bool = _field2method(ma.fields.Bool, "bool")
    str = _field2method(ma.fields.Str, "str")
    float = _field2method(ma.fields.Float, "float")
    decimal = _field2method(ma.fields.Decimal, "decimal")
    list = _field2method(
        _make_list_field,
        "list",
        preprocess=_preprocess_list,
        preprocess_kwarg_names=("subcast", "delimiter"),
    )
    dict = _field2method(
        ma.fields.Dict,
        "dict",
        preprocess=_preprocess_dict,
        preprocess_kwarg_names=(
            "subcast",
            "subcast_keys",
            "subcast_key",
            "subcast_values",
            "delimiter",
        ),
    )
    json = _field2method(ma.fields.Field, "json", preprocess=_preprocess_json)
    datetime = _field2method(ma.fields.DateTime, "datetime")
    date = _field2method(ma.fields.Date, "date")
    time = _field2method(ma.fields.Time, "time")
    path = _field2method(PathField, "path")
    log_level = _field2method(LogLevelField, "log_level")
    timedelta = _field2method(ma.fields.TimeDelta, "timedelta")
    uuid = _field2method(ma.fields.UUID, "uuid")
    url = _field2method(URLField, "url")
    enum = _func2method(_enum_parser, "enum")
    dj_db_url = _func2method(_dj_db_url_parser, "dj_db_url")
    dj_email_url = _func2method(_dj_email_url_parser, "dj_email_url")
    dj_cache_url = _func2method(_dj_cache_url_parser, "dj_cache_url")

    def __init__(self, *, eager: _BoolType = True, expand_vars: _BoolType = False):
        self.eager = eager
        self._sealed: bool = False
        self.expand_vars = expand_vars
        self._fields: typing.Dict[_StrType, typing.Union[ma.fields.Field, type]] = {}
        self._values: typing.Dict[_StrType, typing.Any] = {}
        self._errors: ErrorMapping = collections.defaultdict(list)
        self._prefix: typing.Optional[_StrType] = None
        self.__custom_parsers__: typing.Dict[_StrType, ParserMethod] = {}

    def __repr__(self) -> _StrType:
        return f"<{self.__class__.__name__}(eager={self.eager}, expand_vars={self.expand_vars})>"  # noqa: E501

    @staticmethod
    def read_env(
        path: typing.Optional[_StrType] = None,
        recurse: _BoolType = True,
        verbose: _BoolType = False,
        override: _BoolType = False,
    ) -> _BoolType:
        """Read a .env file into os.environ.

        If .env is not found in the directory from which this method is called,
        the default behavior is to recurse up the directory tree until a .env
        file is found. If you do not wish to recurse up the tree, you may pass
        False as a second positional argument.
        """
        if path is None:
            # By default, start search from the same directory this function is called
            current_frame = inspect.currentframe()
            if current_frame is None:
                raise RuntimeError("Could not get current call frame.")
            frame = current_frame.f_back
            assert frame is not None
            caller_dir = Path(frame.f_code.co_filename).parent.resolve()
            start = caller_dir / ".env"
        else:
            if Path(path).is_dir():
                raise ValueError("path must be a filename, not a directory.")
            start = Path(path)
        if recurse:
            start_dir, env_name = os.path.split(start)
            if not start_dir:  # Only a filename was given
                start_dir = os.getcwd()
            for dirname in _walk_to_root(start_dir):
                check_path = Path(dirname) / env_name
                if check_path.exists():
                    return load_dotenv(check_path, verbose=verbose, override=override)
            return False
        else:
            return load_dotenv(str(start), verbose=verbose, override=override)

    @contextlib.contextmanager
    def prefixed(self, prefix: _StrType) -> typing.Iterator["Env"]:
        """Context manager for parsing envvars with a common prefix."""
        try:
            old_prefix = self._prefix
            if old_prefix is None:
                self._prefix = prefix
            else:
                self._prefix = f"{old_prefix}{prefix}"
            yield self
        finally:
            # explicitly reset the stored prefix on completion and exceptions
            self._prefix = None
        self._prefix = old_prefix

    def seal(self):
        """Validate parsed values and prevent new values from being added.

        :raises: environs.EnvValidationError
        """
        self._sealed = True
        if self._errors:
            error_messages = dict(self._errors)
            self._errors = {}
            raise EnvValidationError(
                f"Environment variables invalid: {error_messages}", error_messages
            )

    def __getattr__(self, name: _StrType):
        try:
            return functools.partial(self.__custom_parsers__[name], self)
        except KeyError as error:
            raise AttributeError(f"{self} has no attribute {name}") from error

    def add_parser(self, name: _StrType, func: typing.Callable) -> None:
        """Register a new parser method with the name ``name``. ``func`` must
        receive the input value for an environment variable.
        """
        if hasattr(self, name):
            raise ParserConflictError(
                f"Env already has a method with name '{name}'. Use a different name."
            )
        self.__custom_parsers__[name] = _func2method(func, method_name=name)
        return None

    def parser_for(
        self, name: _StrType
    ) -> typing.Callable[[typing.Callable], typing.Callable]:
        """Decorator that registers a new parser method with the name ``name``.
        The decorated function must receive the input value for an environment variable.
        """

        def decorator(func: typing.Callable) -> typing.Callable:
            self.add_parser(name, func)
            return func

        return decorator

    def add_parser_from_field(
        self, name: _StrType, field_cls: typing.Type[ma.fields.Field]
    ):
        """Register a new parser method with name ``name``,
        given a marshmallow ``Field``.
        """
        self.__custom_parsers__[name] = _field2method(field_cls, method_name=name)

    def dump(self) -> typing.Mapping[_StrType, typing.Any]:
        """Dump parsed environment variables to a dictionary of simple data types
        (numbers and strings).
        """
        schema = ma.Schema.from_dict(self._fields)()
        return schema.dump(self._values)

    def _get_from_environ(
        self, key: _StrType, default: typing.Any, *, proxied: _BoolType = False
    ) -> typing.Tuple[_StrType, typing.Any, typing.Optional[_StrType]]:
        """Access a value from os.environ. Handles proxied variables,
        e.g. SMTP_LOGIN={{MAILGUN_LOGIN}}.

        Returns a tuple (envvar_key, envvar_value, proxied_key). The ``envvar_key``
        will be different from the passed key for proxied variables. proxied_key
        will be None if the envvar isn't proxied.

        The ``proxied`` flag is recursively passed if a proxy lookup is required
        to get a proxy env key.
        """
        env_key = self._get_key(key, omit_prefix=proxied)
        value = os.environ.get(env_key, default)
        if hasattr(value, "strip"):
            expand_match = self.expand_vars and _EXPANDED_VAR_PATTERN.match(value)
            if expand_match:  # Full match expand_vars - special case keep default
                proxied_key: _StrType = expand_match.groups()[0]
                subs_default: typing.Optional[_StrType] = expand_match.groups()[1]
                if subs_default is not None:
                    default = subs_default[2:]
                elif (
                    value == default
                ):  # if we have used default, don't use it recursively
                    default = ma.missing
                return (
                    key,
                    self._get_from_environ(proxied_key, default, proxied=True)[1],
                    proxied_key,
                )
            expand_search = self.expand_vars and _EXPANDED_VAR_PATTERN.search(value)
            if (
                expand_search
            ):  # Multiple or in text match expand_vars - General case - default lost
                return self._expand_vars(env_key, value)
            # Remove escaped $
            if self.expand_vars and r"\$" in value:
                value = value.replace(r"\$", "$")
        return env_key, value, None

    def _expand_vars(self, parsed_key, value):
        ret = ""
        prev_start = 0
        for match in _EXPANDED_VAR_PATTERN.finditer(value):
            env_key = match.group(1)
            env_default = match.group(2)
            if env_default is None:
                env_default = ma.missing
            else:
                env_default = env_default[2:]  # trim ':-' from default
            _, env_value, _ = self._get_from_environ(env_key, env_default, proxied=True)
            if env_value is ma.missing:
                return parsed_key, env_value, env_key
            ret += value[prev_start : match.start()] + env_value
            prev_start = match.end()
        ret += value[prev_start:]

        return parsed_key, ret, env_key

    def _get_key(self, key: _StrType, *, omit_prefix: _BoolType = False) -> _StrType:
        return self._prefix + key if self._prefix and not omit_prefix else key
