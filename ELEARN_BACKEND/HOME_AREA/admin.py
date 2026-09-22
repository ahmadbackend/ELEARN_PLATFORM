from django.contrib import admin

from .models import COURSES, LECTURES, COMMENTS, PeerChat

admin.site.register(COURSES)
admin.site.register(LECTURES)
admin.site.register(COMMENTS)
admin.site.register(PeerChat)
