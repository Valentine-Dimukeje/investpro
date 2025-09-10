import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env.development")

print("DJANGO_SECRET_KEY =", env("DJANGO_SECRET_KEY", default="MISSING"))
