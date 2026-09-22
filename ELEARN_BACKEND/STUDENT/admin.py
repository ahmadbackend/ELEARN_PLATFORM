from django.contrib import admin

from HOME_AREA.passwords import hash_password, is_hashed
from .models import STUDENT, COURSE_LIST, CODE_GENERATOR


class HashPasswordAdmin(admin.ModelAdmin):
    """Typing a password into the admin stores its hash, not the text.
    An already-hashed value (the normal case when editing another field) is left alone."""

    def save_model(self, request, obj, form, change):
        if obj.PASSWORD and not is_hashed(obj.PASSWORD):
            obj.PASSWORD = hash_password(obj.PASSWORD)
        super().save_model(request, obj, form, change)


@admin.register(STUDENT)
class StudentAdmin(HashPasswordAdmin):
    list_display = ('USER_NAME', 'EMAIL', 'FIRST_NAME', 'LAST_NAME', 'Isactive')
    search_fields = ('USER_NAME', 'EMAIL')
    list_filter = ('Isactive',)


admin.site.register(COURSE_LIST)
admin.site.register(CODE_GENERATOR)
