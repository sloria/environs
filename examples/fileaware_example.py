import os
from tempfile import NamedTemporaryFile

from environs import FileAwareEnv

# Create a secret file
with NamedTemporaryFile(delete=False) as secret_file:
    secret_file.write(b"some secret value")
    secret_file.close()
    os.environ["MYSECRET_FILE"] = str(secret_file.name)

env = FileAwareEnv()

value = env.str("MYSECRET")
assert value == "some secret value"
print(value)

# cleanup
os.unlink(secret_file.name)
