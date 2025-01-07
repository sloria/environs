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
FieldFactory = typing.Callable[..., ma.fields.Field]
Subcast = typing.Union[type[T], typing.Callable[..., T], ma.fields.Field]
ParserMethod = typing.Callable[..., T]


class BaseMethodKwargs(typing.TypedDict, total=False):
    # Subset of relevant marshmallow.Field kwargs shared by all parser methods
    validate: (
        typing.Callable[[typing.Any], typing.Any]
        | typing.Iterable[typing.Callable[[typing.Any], typing.Any]]
        | None
    )
    required: bool


class FieldMethod(typing.Generic[T]):
    @typing.overload
    def __call__(
        self,
        name: str,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> T: ...

    @typing.overload
    def __call__(
        self,
        name: str,
        default: None = ...,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> T | None: ...

    @typing.overload
    def __call__(
        self,
        name: str,
        default: T = ...,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> T: ...

    def __call__(
        self,
        name: str,
        default: typing.Any = ...,
        subcast: Subcast[T] | None = ...,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> T | None: ...


class ListFieldMethod:
    @typing.overload
    def __call__(
        self,
        name: str,
        default: typing.Any = ...,
        subcast: None = ...,
        *,
        delimiter: str | None = ...,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> list[typing.Any] | None: ...

    @typing.overload
    def __call__(
        self,
        name: str,
        default: typing.Any = ...,
        subcast: Subcast[T] = ...,
        *,
        delimiter: str | None = ...,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> list[T] | None: ...

    def __call__(
        self,
        name: str,
        default: typing.Any = ...,
        subcast: Subcast[T] | None = ...,
        *,
        delimiter: str | None = ...,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> list[T] | None: ...


TKeys = typing.TypeVar("TKeys")
TValues = typing.TypeVar("TValues")


class DictFieldMethod:
    def __call__(
        self,
        name: str,
        default: typing.Any = ...,
        *,
        subcast_keys: Subcast[TKeys] | None = None,
        subcast_values: Subcast[TValues] | None = None,
        delimiter: str | None = None,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> dict[TKeys, TValues] | None: ...


class EnumFieldMethod(typing.Generic[EnumT]):
    @typing.overload
    def __call__(
        self,
        name: str,
        *,
        enum: type[EnumT],
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> EnumT: ...

    @typing.overload
    def __call__(
        self,
        name: str,
        default: None = ...,
        *,
        enum: type[EnumT],
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> EnumT | None: ...

    @typing.overload
    def __call__(
        self,
        name: str,
        default: EnumT = ...,
        *,
        enum: type[EnumT],
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> EnumT: ...

    def __call__(
        self,
        name: str,
        default: EnumT | None = ...,
        *,
        enum: type[EnumT],
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> EnumT | None: ...
