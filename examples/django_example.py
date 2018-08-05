"""Example of using environs within a Django settings module.

Requires dj-database-url: pip install dj-database-url

To run this example:

    DEBUG=true SECRET_KEY=myprecious python examples/django_example.py
"""
import os
from pprint import pprint

import environs

env = environs.Env()
try:
    env.read_env()
except IOError:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEBUG = TEMPLATE_DEBUG = env.bool("DEBUG", default=False)

DATABASES = {
    "default": env.dj_db_url(
        "DATABASE_URL",
        default="sqlite:///" + os.path.join(BASE_DIR, "db.sqlite3"),
        ssl_require=not DEBUG,
    )
}

TIME_ZONE = env.str("TIME_ZONE", default="America/Chicago")
USE_L10N = True
USE_TZ = True

# NOTE: Error will be raised if SECRET_KEY is unset
SECRET_KEY = env.str("SECRET_KEY")

EMAIL_HOST = env.str("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default="")
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)

# For demo purposes only
pprint(env.dump(), indent=2)
