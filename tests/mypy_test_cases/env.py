"""Test cases for type hints of environs.Env.

To run these, use: ::

    tox -e mypy-marshmallow3

Or ::

    tox -e mypy-marshmallowdev
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any

import environs

if TYPE_CHECKING:
    import datetime as dt
    import decimal
    import pathlib
    import uuid
    from urllib.parse import ParseResult

env = environs.Env()


class Color(enum.IntEnum):
    RED = 1
    BLUE = 2


INT0: int = env.int("FOO")
INT1: int | None = env.int("FOO", None)
INT2: int = env.int("FOO", 42)

BOOL0: bool | None = env.bool("FOO", None)
STR0: str | None = env.str("FOO", None)
FLOAT0: float | None = env.float("FOO", None)
DECIMAL0: decimal.Decimal | None = env.decimal("FOO", None)
LIST0: list | None = env.list("FOO", None)
LIST1: list[int] | None = env.list("FOO", None, subcast=int)
LIST2: list[Any] = env.list("FOO")
LIST3: list[int] = env.list("FOO", subcast=int)
LIST4: list[int] | bool = env.list("FOO", default=False, subcast=int)
LIST5: list[int] = env.list("FOO", default=[], subcast=int)
DICT0: dict | None = env.dict("FOO", None)
DICT1: dict[str, int] | None = env.dict(
    "FOO",
    None,
    subcast_keys=str,
    subcast_values=int,
)
DICT2: dict[str, int] = env.dict(
    "FOO",
    subcast_keys=str,
    subcast_values=int,
)
DICT3: dict[int, Any] = env.dict(
    "FOO",
    subcast_keys=int,
)
DICT4: dict[Any, int] = env.dict(
    "FOO",
    subcast_values=int,
)
JSON0: list | dict | None = env.json("FOO", None)
DATETIME0: dt.datetime | None = env.datetime("FOO", None)
DATE0: dt.date | None = env.date("FOO", None)
TIME0: dt.time | None = env.time("FOO", None)
TIMEDELTA0: dt.timedelta | None = env.timedelta("FOO", None)
PATH0: pathlib.Path | None = env.path("FOO", None)
LOG_LEVEL0: int | None = env.log_level("FOO", None)
UUID0: uuid.UUID | None = env.uuid("FOO", None)
URL0: ParseResult | None = env.url("FOO", None)
ENUM0: Color = env.enum("FOO", enum=Color)
ENUM1: Color | None = env.enum("FOO", None, enum=Color)
ENUM2: Color = env.enum("FOO", Color.RED, enum=Color)
CALL0: Any = env("FOO", None)
