"""Test cases for type hints of environs.Env.

To run these, use: ::

    tox -e mypy-marshmallow3

Or ::

    tox -e mypy-marshmallowdev
"""

import datetime as dt
import decimal
import pathlib
import uuid
from typing import Any
from urllib.parse import ParseResult

import environs

env = environs.Env()

INT0: int = env.int("FOO")
INT1: int | None = env.int("FOO", None)
INT2: int = env.int("FOO", 42)

BOOL0: bool | None = env.bool("FOO", None)
STR0: str | None = env.str("FOO", None)
FLOAT0: float | None = env.float("FOO", None)
DECIMAL0: decimal.Decimal | None = env.decimal("FOO", None)
LIST0: list | None = env.list("FOO", None)
LIST1: list[int] | None = env.list("FOO", None, subcast=int)
DICT0: dict | None = env.dict("FOO", None)
DICT1: dict[str, int] | None = env.dict(
    "FOO", None, subcast_keys=str, subcast_values=int
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
CALL0: Any = env("FOO", None)
