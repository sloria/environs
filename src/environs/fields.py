"""Custom marshmallow fields for parsing environment variables.

.. warning::
    This module is considered private API.
"""

from __future__ import annotations

import logging
import pathlib
import re
import typing
from datetime import timedelta
from urllib.parse import ParseResult, urlparse

from marshmallow import ValidationError, fields


# TODO: Change to ma.fields.Field[Path] after dropping marshmallow 3 support
class Path(fields.Field):
    def _serialize(self, value: pathlib.Path | None, *args, **kwargs) -> str | None:
        if value is None:
            return None
        return str(value)

    def _deserialize(self, value, *args, **kwargs) -> pathlib.Path:
        if isinstance(value, pathlib.Path):
            return value
        ret = super()._deserialize(value, *args, **kwargs)
        return pathlib.Path(ret)


class LogLevel(fields.Integer):
    def _format_num(self, value) -> int:
        try:
            return super()._format_num(value)
        except (TypeError, ValueError) as error:
            value = value.upper()
            if hasattr(logging, value) and isinstance(getattr(logging, value), int):
                return getattr(logging, value)
            raise ValidationError("Not a valid log level.") from error


class TimeDelta(fields.TimeDelta):
    """Same as marshmallow.fields.TimeDelta but with support for GEP-2257 duration strings."""

    # Ordered duration strings, loosely based on the [GEP-2257](https://gateway-api.sigs.k8s.io/geps/gep-2257/) spec
    # Discrepancies between this pattern and GEP-2257 duration strings:
    # - this pattern accepts units `w|d|h|m|s|ms|[uµ]s` (all units supported by the datetime.timedelta constructor), GEP-2257 accepts only `h|m|s|ms`
    # - this pattern allows for optional whitespace around the units, GEP-2257 does not
    # - this pattern expects ordered (descending) units, GEP-2257 allows arbitrary order
    # - this pattern does not allow duplicate unit occurrences, GEP-2257 does
    # - this pattern allows for negative integers, GEP-2257 does not
    _GEP_2257_REGEX = re.compile(
        r"^(?:\s*)"  # optional whitespace at the beginning of the string
        r"(?:(-?\d+)\s*w\s*)?"  # weeks with optional whitespace around unit
        r"(?:(-?\d+)\s*d\s*)?"  # days with optional whitespace around unit
        r"(?:(-?\d+)\s*h\s*)?"  # hours with optional whitespace around unit
        r"(?:(-?\d+)\s*m\s*)?"  # minutes with optional whitespace around unit
        r"(?:(-?\d+)\s*s\s*)?"  # seconds with optional whitespace around unit
        r"(?:(-?\d+)\s*ms\s*)?"  # milliseconds with optional whitespace around unit
        r"(?:(-?\d+)\s*[µu]s\s*)?$",  # microseconds with optional whitespace around unit
    )

    def _deserialize(self, value, *args, **kwargs) -> timedelta:
        if isinstance(value, timedelta):
            return value
        if isinstance(value, str):
            match = self._GEP_2257_REGEX.match(value)
            if match is not None and any(groups := match.groups(default=0)):
                return timedelta(
                    weeks=int(groups[0]),
                    days=int(groups[1]),
                    hours=int(groups[2]),
                    minutes=int(groups[3]),
                    seconds=int(groups[4]),
                    milliseconds=int(groups[5]),
                    microseconds=int(groups[6]),
                )
        return super()._deserialize(value, *args, **kwargs)


class Url(fields.Url):
    """Same as `marshmallow.fields.Url` but deserializes to a `urllib.parse.ParseResult`."""

    def _serialize(self, value: ParseResult, *args, **kwargs) -> str:  # type: ignore[override]
        return value.geturl()

    # Override deserialize rather than _deserialize because we need
    # to call urlparse *after* validation has occurred
    def deserialize(  # type: ignore[override]
        self,
        value: typing.Any,
        attr: str | None = None,
        data: typing.Mapping[str, typing.Any] | None = None,
        **kwargs,
    ) -> ParseResult:
        ret = typing.cast(str, super().deserialize(value, attr, data, **kwargs))
        return urlparse(ret)
