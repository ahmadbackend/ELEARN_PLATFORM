from django.contrib import admin

from STUDENT.admin import HashPasswordAdmin
from .models import INSTRUCTOR, BLOCK_LIST, CODE_GENERATOR_INSTR


@admin.register(INSTRUCTOR)
class InstructorAdmin(HashPasswordAdmin):
    list_display = ('USER_NAME', 'EMAIL', 'FIRST_NAME', 'LAST_NAME', 'Isactive')
    search_fields = ('USER_NAME', 'EMAIL')
    list_filter = ('Isactive',)


admin.site.register(BLOCK_LIST)
admin.site.register(CODE_GENERATOR_INSTR)
