"""
Authentication backends for the two user tables.

STUDENT and INSTRUCTOR do not extend AbstractBaseUser, so each gets its own
backend. Both verify the submitted password against the stored hash
(HOME_AREA.passwords) -- the password itself is never stored or compared.
"""
from django.contrib.auth.backends import BaseBackend
from django.utils import timezone

from HOME_AREA.passwords import check_user_password
from INSTRUCTOR.models import INSTRUCTOR
from STUDENT.models import STUDENT


class _RoleBackend(BaseBackend):
    model = None

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        user = self.model.objects.filter(EMAIL=username).first()
        if not check_user_password(user, password):
            return None
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        return user

    def get_user(self, user_id):
        return self.model.objects.filter(pk=user_id).first()


class StudentBackend(_RoleBackend):
    model = STUDENT


class InstructorBackend(_RoleBackend):
    model = INSTRUCTOR
