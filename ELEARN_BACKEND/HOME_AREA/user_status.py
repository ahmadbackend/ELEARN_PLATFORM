# the free-text "status" a learner or tutor shows on his dashboard lives in the cache,
# keyed per role so a student and an instructor sharing the same id never overwrite each other
from datetime import timedelta

from django.core.cache import cache

STATUS_TTL = int(timedelta(days=30).total_seconds())


def status_cache_key(user):
    return f'user_status_{user.user_cat}_{user.id}'


def get_status(user):
    return cache.get(status_cache_key(user))


def set_status(user, text):
    cache.set(status_cache_key(user), text, timeout=STATUS_TTL)


def clear_status(user):
    cache.delete(status_cache_key(user))
