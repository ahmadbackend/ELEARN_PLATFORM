"""
Password storage for STUDENT and INSTRUCTOR.

Neither model extends AbstractBaseUser, so they get no `set_password` /
`check_password` of their own. Both columns hold a Django password hash
(PBKDF2 by default) produced by these two helpers; nothing writes a raw
password to the database.

The plaintext rules users must satisfy still live on the model field
(MinLengthValidator + RegexValidator), because the serializers read their
validators back off the field to validate the *raw* input before hashing.
"""
from django.contrib.auth.hashers import (
    check_password as _check_password,
    identify_hasher,
    make_password,
)

# a hash is much longer than the 12 raw characters the rules allow
PASSWORD_HASH_MAX_LENGTH = 128


def hash_password(raw):
    """Hash a raw password for storage."""
    return make_password(raw)


def is_hashed(value):
    """True when `value` already looks like a Django password hash."""
    if not value:
        return False
    try:
        identify_hasher(value)
    except ValueError:
        return False
    return True


def set_password(user, raw, save=True):
    """Hash `raw` onto `user.PASSWORD`, saving just that column by default."""
    user.PASSWORD = hash_password(raw)
    if save:
        user.save(update_fields=['PASSWORD'])
    return user


def check_user_password(user, raw):
    """Constant-time check of `raw` against the stored hash."""
    if user is None or not raw:
        return False
    return _check_password(raw, user.PASSWORD)
