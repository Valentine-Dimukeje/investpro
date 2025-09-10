import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
env = environ.Env()

env_file = BASE_DIR / ".env.development"
print("Looking for:", env_file, "Exists?", env_file.exists())

environ.Env.read_env(env_file)

print("DJANGO_SECRET_KEY =", env("DJANGO_SECRET_KEY", default="MISSING"))
