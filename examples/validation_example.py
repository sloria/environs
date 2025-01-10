import os

from environs import EnvError, ValidationError, env, validate

os.environ["TTL"] = "-2"
os.environ["NODE_ENV"] = "invalid"
os.environ["EMAIL"] = "^_^"

# built-in validator
try:
    env.str(
        "NODE_ENV",
        validate=validate.OneOf(
            ["production", "development"], error="NODE_ENV must be one of: {choices}"
        ),
    )
except EnvError as err:
    print(err)


# multiple validators
try:
    env.str("EMAIL", validate=[validate.Length(min=4), validate.Email()])
except EnvError as err:
    print(err)


# custom validator
def validate_ttl(value):
    if value <= 0:
        raise ValidationError("TTL must be greater than 0")
    return value


try:
    env.int("TTL", validate=validate_ttl)
except EnvError as err:
    print(err)
