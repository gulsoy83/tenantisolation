import os

from environs import Env

env = Env()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env.read_env(os.path.join(BASE_DIR, ".env"))

DEBUG = env.bool("DEBUG", False)
SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", ["127.0.0.1", "localhost"])
CORS_ORIGIN_WHITELIST = env.list("CORS_ORIGIN_WHITELIST", ["localhost"])
CORS_ORIGIN_REGEX_WHITELIST = os.getenv("CORS_ORIGIN_REGEX_WHITELIST")
CORS_ORIGIN_ALLOW_ALL = os.getenv("CORS_ORIGIN_ALLOW_ALL")

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", [])
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", True)
CSRF_USE_SESSIONS = True

SESSION_ENGINE = os.getenv("SESSION_ENGINE", "django.contrib.sessions.backends.db")
SESSION_CACHE_ALIAS = os.getenv("SESSION_CACHE_ALIAS", "default")
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", True)
SESSION_COOKIE_NAME = env.str("SESSION_COOKIE_NAME", "sessionid")

# REDIS CACHE SETTINGS
REDIS_BACKEND = os.getenv("REDIS_BACKEND", "django_redis.cache.RedisCache")
REDIS_SERVER = os.getenv("REDIS_SERVER")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_DB = os.getenv("REDIS_DB")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_CONNECT_TIMEOUT = os.getenv("REDIS_CONNECT_TIMEOUT", 5)
REDIS_SOCKET_TIMEOUT = os.getenv("SOCKET_TIMEOUT", 5)

# CACHE SETTINGS
CACHE_BACKEND = os.getenv("CACHE_BACKEND", "redis")


POSTGRES_SERVER = os.getenv("POSTGRES_SERVER")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")