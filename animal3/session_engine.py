
from django.contrib.sessions.backends.cache import SessionStore as CacheSessionStore


class SessionStore(CacheSessionStore):
    cache_key_prefix = ''
