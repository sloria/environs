import os

from envargs import Env

# Prefixed envvars
os.environ['CANTEEN_HOST'] = 'lolcathost'
os.environ['CANTEEN_PORT'] = '3000'
# A non-prefixed envvar
os.environ['NODE_ENV'] = 'production'


env = Env()
with env.prefixed('CANTEEN_'):
    host = env.str('HOST', 'localhost')
    port = env.int('PORT', 5000)
node_env = env.str('NODE_ENV', 'development')


assert host == 'lolcathost'
assert port == 3000
assert node_env == 'production'
print(env.dump())
