import os
try:
    import urllib.parse as urlparse
except ImportError:
    # Python 2
    import urlparse

from furl import furl as Furl
from envargs import Env

##### This is the beginning of the plugin code #####

def furl_parser(value):
    return Furl(value)

def urlparse_parser(value):
    return urlparse.urlparse(value)

def setup(env):
    env.add_parser('furl', furl_parser)
    env.add_parser('purl', urlparse_parser)

##### End of the plugin code #####

os.environ['GITHUB_URL'] = 'https://github.com/sloria/envargs'

# Our application activates the plugin using the setup function

env = Env()
setup(env)

# We now have the 'furl' and 'purl' methods available

github_furl = env.furl('GITHUB_URL')
github_purl = env.purl('GITHUB_URL')
