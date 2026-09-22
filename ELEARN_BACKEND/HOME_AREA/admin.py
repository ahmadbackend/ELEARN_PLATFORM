from django.contrib import admin

from .models import COURSES, LECTURES, COMMENTS, PeerChat, REVIEWS, Rating


class LectureInline(admin.TabularInline):
    model = LECTURES
    extra = 0
    fields = ('NAME', 'VIDEO', 'ADDITIONAL_FILES')


@admin.register(COURSES)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('COURSE_NAME', 'instructor', 'IsDraft', 'PUBLICATION_DATE', 'lecture_count')
    list_filter = ('IsDraft',)
    search_fields = ('COURSE_NAME', 'instructor__USER_NAME')
    list_select_related = ('instructor',)
    readonly_fields = ('PUBLICATION_DATE',)
    date_hierarchy = 'PUBLICATION_DATE'
    inlines = [LectureInline]

    @admin.display(description='lectures')
    def lecture_count(self, course):
        return course.lectures.count()


@admin.register(LECTURES)
class LectureAdmin(admin.ModelAdmin):
    list_display = ('NAME', 'course')
    search_fields = ('NAME', 'course__COURSE_NAME')
    list_select_related = ('course',)


@admin.register(REVIEWS)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('USER_NAME', 'reviews', 'WRITING_DATE', 'excerpt')
    search_fields = ('USER_NAME__USER_NAME', 'reviews__COURSE_NAME', 'OPINION')
    list_select_related = ('USER_NAME', 'reviews')
    readonly_fields = ('WRITING_DATE',)
    date_hierarchy = 'WRITING_DATE'

    @admin.display(description='opinion')
    def excerpt(self, review):
        text = review.OPINION or ''
        return text[:80] + ('…' if len(text) > 80 else '')


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'RATING')
    list_filter = ('RATING',)
    list_select_related = ('user', 'course')


@admin.register(PeerChat)
class PeerChatAdmin(admin.ModelAdmin):
    """Read-only apart from deletion: a moderator takes messages down, never edits them."""
    list_display = ('TimeStamp', 'instructor', 'student', 'sender_cat', 'excerpt')
    search_fields = ('message', 'instructor__USER_NAME', 'student__USER_NAME')
    list_select_related = ('instructor', 'student', 'content_type')
    readonly_fields = ('student', 'instructor', 'message', 'content_type', 'object_id', 'TimeStamp')
    date_hierarchy = 'TimeStamp'

    def has_add_permission(self, request):
        return False

    @admin.display(description='message')
    def excerpt(self, chat):
        return chat.message[:80] + ('…' if len(chat.message) > 80 else '')


@admin.register(COMMENTS)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('USER_NAME', 'discussion', 'WRITING_DATE')
    search_fields = ('COMMENT', 'USER_NAME__USER_NAME')
    readonly_fields = ('WRITING_DATE',)
