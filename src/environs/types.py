"""Custom types and type aliases.

.. warning::

    This module is provisional. Types may be modified, added, and removed between minor releases.
"""

import enum
import typing

import marshmallow as ma

T = typing.TypeVar("T")
EnumT = typing.TypeVar("EnumT", bound=enum.Enum)


ErrorMapping = typing.Mapping[str, list[str]]
ErrorList = list[str]
FieldFactory = typing.Callable[..., ma.fields.Field]
Subcast = typing.Union[type, typing.Callable[..., T], ma.fields.Field]
FieldType = type[ma.fields.Field]
FieldOrFactory = typing.Union[FieldType, FieldFactory]
ParserMethod = typing.Callable[..., T]


class FieldMethod(typing.Generic[T]):
    def __call__(
        self,
        name: str,
        default: typing.Any = ma.missing,
        subcast: Subcast[T] | None = None,
        *,
        # Subset of relevant marshmallow.Field kwargs
        load_default: typing.Any = ma.missing,
        validate: (
            typing.Callable[[typing.Any], typing.Any]
            | typing.Iterable[typing.Callable[[typing.Any], typing.Any]]
            | None
        ) = None,
        required: bool = False,
        allow_none: bool | None = None,
        error_messages: dict[str, str] | None = None,
        metadata: typing.Mapping[str, typing.Any] | None = None,
    ) -> T | None: ...


class ListFieldMethod:
    def __call__(
        self,
        name: str,
        default: typing.Any = ma.missing,
        subcast: Subcast[T] | None = None,
        *,
        # Subset of relevant marshmallow.Field kwargs
        load_default: typing.Any = ma.missing,
        validate: (
            typing.Callable[[typing.Any], typing.Any]
            | typing.Iterable[typing.Callable[[typing.Any], typing.Any]]
            | None
        ) = None,
        required: bool = False,
        allow_none: bool | None = None,
        error_messages: dict[str, str] | None = None,
        metadata: typing.Mapping[str, typing.Any] | None = None,
        delimiter: str | None = None,
    ) -> list | None: ...


class DictFieldMethod:
    def __call__(
        self,
        name: str,
        default: typing.Any = ma.missing,
        *,
        # Subset of relevant marshmallow.Field kwargs
        load_default: typing.Any = ma.missing,
        validate: typing.Callable[[typing.Any], typing.Any]
        | typing.Iterable[typing.Callable[[typing.Any], typing.Any]]
        | None = None,
        required: bool = False,
        allow_none: bool | None = None,
        error_messages: dict[str, str] | None = None,
        metadata: typing.Mapping[str, typing.Any] | None = None,
        subcast_keys: Subcast[T] | None = None,
        subcast_values: Subcast[T] | None = None,
        delimiter: str | None = None,
    ) -> dict | None: ...


class EnumFuncMethod:
    def __call__(
        self,
        value,
        type: type[EnumT],
        default: EnumT | None = None,
        ignore_case: bool = False,
    ) -> EnumT | None: ...
