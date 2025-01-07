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

A: int | None = env.int("FOO", None)
B: bool | None = env.bool("FOO", None)
C: str | None = env.str("FOO", None)
D: float | None = env.float("FOO", None)
E: decimal.Decimal | None = env.decimal("FOO", None)
F: list | None = env.list("FOO", None)
G: list[int] | None = env.list("FOO", None, subcast=int)
H: dict | None = env.dict("FOO", None)
J: dict[str, int] | None = env.dict("FOO", None, subcast_keys=str, subcast_values=int)
K: list | dict | None = env.json("FOO", None)
L: dt.datetime | None = env.datetime("FOO", None)
M: dt.date | None = env.date("FOO", None)
N: dt.time | None = env.time("FOO", None)
P: dt.timedelta | None = env.timedelta("FOO", None)
Q: pathlib.Path | None = env.path("FOO", None)
R: int | None = env.log_level("FOO", None)
S: uuid.UUID | None = env.uuid("FOO", None)
T: ParseResult | None = env.url("FOO", None)
U: Any = env("FOO", None)
