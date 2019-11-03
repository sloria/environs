import os
from pprint import pprint

from environs import Env, EnvValidationError
from marshmallow.validate import OneOf, Email, Length, Range


os.environ["TTL"] = "-2"
os.environ["NODE_ENV"] = "invalid"
os.environ["EMAIL"] = "^_^"


env = Env(eager=False)
TTL = env.int("TTL", validate=Range(min=0, max=100))
NODE_ENV = env.str(
    "NODE_ENV", validate=OneOf(["production", "development"], error="NODE_ENV must be one of: {choices}")
)
EMAIL = env.str("EMAIL", validate=[Length(min=4), Email()])

# This will raise an error with the combined validation messages
try:
    env.seal()
except EnvValidationError as error:
    pprint(error.error_messages)
