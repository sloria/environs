"""Example of using environs within a Django settings module.

Requires dj-database-url: pip install dj-database-url

To run this example:

    DEBUG=true SECRET_KEY=myprecious python examples/django_example.py
"""

import os
from pprint import pprint

from environs import env

env.read_env()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Override in .env for local development
DEBUG = TEMPLATE_DEBUG = env.bool("DEBUG", default=False)

# NOTE: Error will be raised if SECRET_KEY is unset
SECRET_KEY = env.str("SECRET_KEY")

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

email = env.dj_email_url("EMAIL_URL", default="smtp://")
EMAIL_HOST = email["EMAIL_HOST"]
EMAIL_PORT = email["EMAIL_PORT"]
EMAIL_HOST_PASSWORD = email["EMAIL_HOST_PASSWORD"]
EMAIL_HOST_USER = email["EMAIL_HOST_USER"]
EMAIL_USE_TLS = email["EMAIL_USE_TLS"]

# For demo purposes only
pprint(env.dump(), indent=2)
