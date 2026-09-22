"""
Role permissions for the REST API. request.user is a STUDENT or INSTRUCTOR instance
(or AnonymousUser), so every check goes through `user_cat` instead of Django groups.
"""
from rest_framework.permissions import BasePermission


def user_cat(user):
    return getattr(user, 'user_cat', None)


class IsStudent(BasePermission):
    message = 'Only students can perform this action.'

    def has_permission(self, request, view):
        return user_cat(request.user) == 'student'


class IsInstructor(BasePermission):
    message = 'Only instructors can perform this action.'

    def has_permission(self, request, view):
        return user_cat(request.user) == 'instructor'
