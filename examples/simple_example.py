import os
from pprint import pprint

from envargs import Env


os.environ['GITHUB_USER'] = 'sloria'
os.environ['API_KEY'] = '123abc'
os.environ['SHIP_DATE'] = '1984-06-25'
os.environ['ENABLE_LOGIN'] = 'true'
os.environ['MAX_CONNECTIONS'] = '42'
os.environ['GITHUB_REPOS'] = 'webargs,konch,ped'
os.environ['COORDINATES'] = '23.3,50.0'
os.environ['MYAPP_HOST'] = 'lolcathost'
os.environ['MYAPP_PORT'] = '3000'


env = Env()
# reading an environment variable
gh_user = env('GITHUB_USER')  # => 'sloria'
# casting
api_key = env.str('API_KEY')  # => '123abc'
date = env.date('SHIP_DATE')  # => datetime.date(1984, 6, 25)
# providing a default value
enable_login = env.bool('ENABLE_LOGIN', False)  # => True
enable_feature_x = env.bool('ENABLE_FEATURE_X', False)  # => False
# parsing lists
gh_repos = env.list('GITHUB_REPOS')  # => ['webargs', 'konch', 'ped']
coords = env.list('COORDINATES', subcast=float)  # => [23.3, 50.0]

with env.prefixed('MYAPP_'):
    host = env('HOST', 'localhost')
    port = env.int('PORT', 5000)

pprint(env.dump(), indent=2)
