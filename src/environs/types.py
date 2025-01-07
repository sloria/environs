"""Custom types and type aliases.

.. warning::

    This module is provisional. Types may be modified, added, and removed between minor releases.
"""

from __future__ import annotations

import enum
import typing

try:
    from typing import Unpack
except ImportError:  # Remove when dropping Python 3.10
    from typing_extensions import Unpack

import marshmallow as ma

T = typing.TypeVar("T")
EnumT = typing.TypeVar("EnumT", bound=enum.Enum)


ErrorMapping = typing.Mapping[str, list[str]]
ErrorList = list[str]
FieldFactory = typing.Callable[..., ma.fields.Field]
Subcast = typing.Union[type[T], typing.Callable[..., T], ma.fields.Field]
FieldType = type[ma.fields.Field]
FieldOrFactory = typing.Union[FieldType, FieldFactory]
ParserMethod = typing.Callable[..., T]


class BaseMethodKwargs(typing.TypedDict, total=False):
    # Subset of relevant marshmallow.Field kwargs shared by all parser methods
    validate: (
        typing.Callable[[typing.Any], typing.Any]
        | typing.Iterable[typing.Callable[[typing.Any], typing.Any]]
        | None
    )
    required: bool
    error_messages: dict[str, str] | None
    metadata: typing.Mapping[str, typing.Any] | None


class FieldMethod(typing.Generic[T]):
    @typing.overload
    def __call__(
        self,
        name: str,
        default: typing.Any = ...,
        subcast: Subcast[T] | None = ...,
        *,
        allow_none: typing.Literal[False],
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> T: ...

    @typing.overload
    def __call__(
        self,
        name: str,
        default: T,
        subcast: Subcast[T] | None = None,
        *,
        allow_none: bool | None = None,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> T: ...

    @typing.overload
    def __call__(
        self,
        name: str,
        default: None = ...,
        subcast: Subcast[T] | None = ...,
        *,
        allow_none: bool | None = ...,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> T | None: ...

    def __call__(
        self,
        name: str,
        default: typing.Any = ma.missing,
        subcast: Subcast[T] | None = None,
        *,
        allow_none: bool | None = None,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> T | None: ...


class ListFieldMethod:
    @typing.overload
    def __call__(
        self,
        name: str,
        default: typing.Any = ma.missing,
        subcast: None = ...,
        *,
        delimiter: str | None = None,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> list[typing.Any] | None: ...

    @typing.overload
    def __call__(
        self,
        name: str,
        default: typing.Any = ma.missing,
        subcast: Subcast[T] = ...,
        *,
        delimiter: str | None = None,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> list[T] | None: ...

    def __call__(
        self,
        name: str,
        default: typing.Any = ma.missing,
        subcast: Subcast[T] | None = None,
        *,
        delimiter: str | None = None,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> list[T] | None: ...


TKeys = typing.TypeVar("TKeys")
TValues = typing.TypeVar("TValues")


class DictFieldMethod:
    def __call__(
        self,
        name: str,
        default: typing.Any = ma.missing,
        *,
        subcast_keys: Subcast[TKeys] | None = None,
        subcast_values: Subcast[TValues] | None = None,
        delimiter: str | None = None,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> dict[TKeys, TValues] | None: ...


class EnumFuncMethod:
    def __call__(
        self,
        value,
        type: type[EnumT],
        default: EnumT | None = None,
        ignore_case: bool = False,
    ) -> EnumT | None: ...
