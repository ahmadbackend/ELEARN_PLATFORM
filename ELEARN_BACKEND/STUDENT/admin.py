from django.contrib import admin

from HOME_AREA.passwords import hash_password, is_hashed
from .models import STUDENT, COURSE_LIST, CODE_GENERATOR


class HashPasswordAdmin(admin.ModelAdmin):
    """Shared by the STUDENT and INSTRUCTOR admins.

    Typing a password into the form stores its hash, not the text, and an
    already-hashed value (the normal case when editing another field) is left
    alone. The field itself is only offered to superusers: a moderator can
    suspend an account but must not be able to set its password and sign in as
    that person.
    """

    def get_exclude(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            return ('PASSWORD',)
        return super().get_exclude(request, obj)

    def save_model(self, request, obj, form, change):
        if obj.PASSWORD and not is_hashed(obj.PASSWORD):
            obj.PASSWORD = hash_password(obj.PASSWORD)
        super().save_model(request, obj, form, change)


@admin.register(STUDENT)
class StudentAdmin(HashPasswordAdmin):
    list_display = ('USER_NAME', 'FIRST_NAME', 'LAST_NAME', 'EMAIL', 'PHONE', 'Isactive', 'last_login')
    list_filter = ('Isactive',)
    search_fields = ('USER_NAME', 'EMAIL', 'FIRST_NAME', 'LAST_NAME')
    readonly_fields = ('last_login',)
    ordering = ('USER_NAME',)


@admin.register(COURSE_LIST)
class EnrolmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course')
    list_select_related = ('student', 'course')
    search_fields = ('student__USER_NAME', 'course__COURSE_NAME')


@admin.register(CODE_GENERATOR)
class ActivationCodeAdmin(admin.ModelAdmin):
    list_display = ('EMAIL', 'USER_VERIFIER', 'ACTIVATION_CODE')
    search_fields = ('EMAIL',)
