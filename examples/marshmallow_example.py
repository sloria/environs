import os
import pathlib

import marshmallow as ma
from environs import Env


os.environ["STATIC_PATH"] = "app/static"


class PathField(ma.fields.Field):
    def _deserialize(self, value, *args, **kwargs):
        return pathlib.Path(value)

    def _serialize(self, value, *args, **kwargs):
        return str(value)


env = Env()
env.parser_from_field("path", PathField)

static_path = env.path("STATIC_PATH")
assert isinstance(static_path, pathlib.Path)

print(env.dump())
