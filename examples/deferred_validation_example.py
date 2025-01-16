import os
from pprint import pprint

from environs import Env, EnvValidationError, validate

os.environ["TTL"] = "-2"
os.environ["NODE_ENV"] = "invalid"
os.environ["EMAIL"] = "^_^"


env = Env(eager=False)
TTL = env.int("TTL", validate=validate.Range(min=0, max=100))
NODE_ENV = env.str(
    "NODE_ENV",
    validate=validate.OneOf(
        ["production", "development"], error="NODE_ENV must be one of: {choices}",
    ),
)
EMAIL = env.str("EMAIL", validate=[validate.Length(min=4), validate.Email()])

# This will raise an error with the combined validation messages
try:
    env.seal()
except EnvValidationError as error:
    pprint(error.error_messages)
