import os

from furl import furl as Furl  # noqa: N812
from yarl import URL

from environs import env

##### This is the beginning of the plugin code #####


def furl_parser(value):
    return Furl(value)


def urlparse_parser(value):
    return URL(value)


def setup(env):
    env.add_parser("furl", furl_parser)
    env.add_parser("yurl", urlparse_parser)


##### End of the plugin code #####


os.environ["GITHUB_URL"] = "https://github.com/sloria/environs"

# Our application activates the plugin using the setup function

setup(env)

# We now have the 'furl' and 'yurl' methods available

github_furl = env.furl("GITHUB_URL")
github_yurl = env.yurl("GITHUB_URL")
