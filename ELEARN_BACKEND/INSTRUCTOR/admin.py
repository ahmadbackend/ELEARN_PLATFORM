from django.contrib import admin

from STUDENT.admin import HashPasswordAdmin
from .models import INSTRUCTOR, BLOCK_LIST, CODE_GENERATOR_INSTR


@admin.register(INSTRUCTOR)
class InstructorAdmin(HashPasswordAdmin):
    list_display = ('USER_NAME', 'FIRST_NAME', 'LAST_NAME', 'EMAIL', 'PHONE', 'Isactive', 'last_login')
    list_filter = ('Isactive',)
    search_fields = ('USER_NAME', 'EMAIL', 'FIRST_NAME', 'LAST_NAME')
    readonly_fields = ('last_login',)
    ordering = ('USER_NAME',)


@admin.register(BLOCK_LIST)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('students', 'instructors')
    list_select_related = ('students', 'instructors')
    search_fields = ('students__USER_NAME', 'instructors__USER_NAME')


@admin.register(CODE_GENERATOR_INSTR)
class ActivationCodeAdmin(admin.ModelAdmin):
    list_display = ('EMAIL', 'USER_VERIFIER', 'ACTIVATION_CODE')
    search_fields = ('EMAIL',)
