"""
Serializers shared by every part of the API: users, courses and the auth flows.
Field names mirror the model columns (COURSE_NAME, COVER_PHOTO, ...) so the JSON a
frontend sees is exactly what the database stores.
"""
from django.db.models import Avg, Count
from django.utils.module_loading import import_string
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from INSTRUCTOR.models import INSTRUCTOR, CODE_GENERATOR_INSTR, BLOCK_LIST
from STUDENT.models import STUDENT, CODE_GENERATOR, COURSE_LIST
from .models import COURSES, LECTURES, REVIEWS, Rating, PeerChat
from .passwords import hash_password

USER_TYPES = (('student', 'student'), ('instructor', 'instructor'))
# per-role lookups so the auth views never branch on strings themselves
USER_MODEL = {'student': STUDENT, 'instructor': INSTRUCTOR}
CODE_MODEL = {'student': CODE_GENERATOR, 'instructor': CODE_GENERATOR_INSTR}
AUTH_BACKEND = {'student': 'HOME_AREA.AuthCust.StudentBackend',
                'instructor': 'HOME_AREA.AuthCust.InstructorBackend'}


# ----------------------------------------------------------------------------- users
class StudentPublicSerializer(serializers.ModelSerializer):
    user_cat = serializers.CharField(read_only=True)

    class Meta:
        model = STUDENT
        fields = ['id', 'USER_NAME', 'FIRST_NAME', 'LAST_NAME', 'PICTURE', 'user_cat']
        read_only_fields = fields


class InstructorPublicSerializer(serializers.ModelSerializer):
    user_cat = serializers.CharField(read_only=True)

    class Meta:
        model = INSTRUCTOR
        fields = ['id', 'USER_NAME', 'FIRST_NAME', 'LAST_NAME', 'PICTURE', 'user_cat']
        read_only_fields = fields


def public_user_serializer(user):
    return StudentPublicSerializer if user.user_cat == 'student' else InstructorPublicSerializer


class _PasswordMixin:
    """Validates the raw password against the model column's rules and hashes it before
    it is written. Fields are declared per class: DRF only collects declared fields from
    Serializer bases, not from plain mixins."""

    def validate_PASSWORD(self, value):
        # reuse the validators declared on the model column
        field = self.Meta.model._meta.get_field('PASSWORD')
        for validator in field.validators:
            validator(value)
        return value

    def _hash(self, validated_data):
        # the column stores a hash; the raw password never reaches the database
        if validated_data.get('PASSWORD'):
            validated_data['PASSWORD'] = hash_password(validated_data['PASSWORD'])
        return validated_data

    def create(self, validated_data):
        return super().create(self._hash(validated_data))

    def update(self, instance, validated_data):
        return super().update(instance, self._hash(validated_data))


class StudentPrivateSerializer(_PasswordMixin, serializers.ModelSerializer):
    user_cat = serializers.CharField(read_only=True)
    PASSWORD = serializers.CharField(write_only=True, required=False, min_length=8, max_length=12)

    class Meta:
        model = STUDENT
        fields = ['id', 'USER_NAME', 'FIRST_NAME', 'LAST_NAME', 'EMAIL', 'PHONE', 'PICTURE',
                  'PASSWORD', 'last_login', 'user_cat']
        read_only_fields = ['id', 'USER_NAME', 'EMAIL', 'last_login']


class InstructorPrivateSerializer(_PasswordMixin, serializers.ModelSerializer):
    user_cat = serializers.CharField(read_only=True)
    PASSWORD = serializers.CharField(write_only=True, required=False, min_length=8, max_length=12)

    class Meta:
        model = INSTRUCTOR
        fields = ['id', 'USER_NAME', 'FIRST_NAME', 'LAST_NAME', 'EMAIL', 'PHONE', 'PICTURE',
                  'PASSWORD', 'last_login', 'user_cat']
        read_only_fields = ['id', 'USER_NAME', 'EMAIL', 'last_login']


def private_user_serializer(user):
    return StudentPrivateSerializer if user.user_cat == 'student' else InstructorPrivateSerializer


# ----------------------------------------------------------------------------- auth flows
class StudentRegisterSerializer(_PasswordMixin, serializers.ModelSerializer):
    PASSWORD = serializers.CharField(write_only=True, min_length=8, max_length=12)

    class Meta:
        model = STUDENT
        fields = ['id', 'FIRST_NAME', 'LAST_NAME', 'USER_NAME', 'EMAIL', 'PHONE', 'PASSWORD', 'PICTURE']
        extra_kwargs = {'PICTURE': {'required': False}}


class InstructorRegisterSerializer(_PasswordMixin, serializers.ModelSerializer):
    PASSWORD = serializers.CharField(write_only=True, min_length=8, max_length=12)

    class Meta:
        model = INSTRUCTOR
        fields = ['id', 'FIRST_NAME', 'LAST_NAME', 'USER_NAME', 'EMAIL', 'PHONE', 'PASSWORD', 'PICTURE']


class LoginSerializer(serializers.Serializer):
    user_type = serializers.ChoiceField(choices=USER_TYPES)
    EMAIL = serializers.EmailField()
    PASSWORD = serializers.CharField(write_only=True)

    def validate(self, data):
        # same backends the MVT login uses, but only the one for this role: django's
        # authenticate() would try every backend and ignore the `backend=` hint
        backend = import_string(AUTH_BACKEND[data['user_type']])()
        user = backend.authenticate(self.context.get('request'), username=data['EMAIL'],
                                    password=data['PASSWORD'])
        if user is None:
            raise serializers.ValidationError('Wrong email or password.')
        # an inactive account is reported by the view (403 + Isactive flag) so the SPA can
        # route to the activation screen instead of showing a validation error
        data['user'] = user
        return data


class ActivateSerializer(serializers.Serializer):
    user_type = serializers.ChoiceField(choices=USER_TYPES)
    EMAIL = serializers.EmailField()
    ACTIVATION_CODE = serializers.CharField(max_length=6)


class ForgotPasswordSerializer(serializers.Serializer):
    user_type = serializers.ChoiceField(choices=USER_TYPES)
    EMAIL = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    user_type = serializers.ChoiceField(choices=USER_TYPES)
    EMAIL = serializers.EmailField()
    ACTIVATION_CODE = serializers.CharField(max_length=6)
    PASSWORD = serializers.CharField(write_only=True, min_length=8, max_length=12)
    CONFIRM_PASSWORD = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['PASSWORD'] != data['CONFIRM_PASSWORD']:
            raise serializers.ValidationError({'CONFIRM_PASSWORD': 'Passwords do not match.'})
        for validator in USER_MODEL[data['user_type']]._meta.get_field('PASSWORD').validators:
            validator(data['PASSWORD'])
        return data


class TokenResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    expires_in = serializers.IntegerField(help_text='seconds')
    user = serializers.DictField()


class StatusSerializer(serializers.Serializer):
    status = serializers.CharField(max_length=500, allow_blank=True)


class MessageSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000)


class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


# ----------------------------------------------------------------------------- courses
def rating_summary(course):
    agg = course.rating_set.aggregate(average=Avg('RATING'), count=Count('id'))
    breakdown = {str(n): 0 for n in range(1, 6)}
    for row in course.rating_set.values('RATING').annotate(n=Count('id')):
        if row['RATING'] is not None:
            breakdown[str(row['RATING'])] = row['n']
    return {'average': round(agg['average'], 2) if agg['average'] is not None else 0,
            'count': agg['count'], 'breakdown': breakdown}


class RatingSummarySerializer(serializers.Serializer):
    """Shape of the `rating` block on a course; documentation only, never used to write."""
    average = serializers.FloatField()
    count = serializers.IntegerField()
    breakdown = serializers.DictField(child=serializers.IntegerField(),
                                      help_text='how many ratings per star, keyed "1".."5"')


class CourseViewerSerializer(serializers.Serializer):
    """Shape of the `viewer` block: what the caller may do with this course."""
    user_cat = serializers.CharField(allow_null=True)
    is_owner = serializers.BooleanField()
    enrolled = serializers.BooleanField()
    blocked = serializers.BooleanField()
    can_watch = serializers.BooleanField()


class LectureSerializer(serializers.ModelSerializer):
    class Meta:
        model = LECTURES
        fields = ['id', 'NAME', 'VIDEO', 'ADDITIONAL_FILES', 'course']
        read_only_fields = ['course']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # only enrolled learners and the owner get the media urls, everybody else sees the outline
        if not self.context.get('can_watch', False):
            data['VIDEO'] = None
            data['ADDITIONAL_FILES'] = None
        return data


class CourseListSerializer(serializers.ModelSerializer):
    instructor = InstructorPublicSerializer(read_only=True)
    rating = serializers.SerializerMethodField()
    lecture_count = serializers.IntegerField(read_only=True)
    enrolled_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = COURSES
        fields = ['id', 'COURSE_NAME', 'COVER_PHOTO', 'instructor', 'PUBLICATION_DATE', 'IsDraft',
                 'rating', 'lecture_count', 'enrolled_count']
        read_only_fields = fields

    @extend_schema_field(RatingSummarySerializer)
    def get_rating(self, course):
        return rating_summary(course)


class ReviewSerializer(serializers.ModelSerializer):
    USER_NAME = StudentPublicSerializer(read_only=True)

    class Meta:
        model = REVIEWS
        fields = ['id', 'USER_NAME', 'OPINION', 'WRITING_DATE']
        read_only_fields = ['id', 'USER_NAME', 'WRITING_DATE']
        extra_kwargs = {'OPINION': {'required': True, 'allow_blank': False, 'allow_null': False}}


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['id', 'RATING']
        extra_kwargs = {'RATING': {'required': True, 'allow_null': False}}


class CourseDetailSerializer(CourseListSerializer):
    lectures = serializers.SerializerMethodField()
    viewer = serializers.SerializerMethodField()

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ['lectures', 'viewer']
        read_only_fields = fields

    def viewer_flags(self, course):
        """What the current user may do with this course. Cached per serializer instance."""
        if hasattr(self, '_viewer'):
            return self._viewer
        user = self.context['request'].user
        cat = getattr(user, 'user_cat', None)
        flags = {'user_cat': cat, 'is_owner': False, 'enrolled': False, 'blocked': False}
        if cat == 'student':
            flags['enrolled'] = COURSE_LIST.objects.filter(course=course, student=user).exists()
            flags['blocked'] = BLOCK_LIST.objects.filter(students=user, instructors=course.instructor).exists()
        elif cat == 'instructor':
            flags['is_owner'] = course.instructor_id == user.id
        flags['can_watch'] = flags['is_owner'] or (flags['enrolled'] and not flags['blocked'])
        self._viewer = flags
        return flags

    @extend_schema_field(CourseViewerSerializer)
    def get_viewer(self, course):
        return self.viewer_flags(course)

    @extend_schema_field(LectureSerializer(many=True))
    def get_lectures(self, course):
        ctx = dict(self.context, can_watch=self.viewer_flags(course)['can_watch'])
        return LectureSerializer(course.lectures.all(), many=True, context=ctx).data


class CourseWriteSerializer(serializers.ModelSerializer):
    """Instructor create/update. `instructor` is always taken from the request."""

    class Meta:
        model = COURSES
        fields = ['id', 'COURSE_NAME', 'COVER_PHOTO', 'IsDraft', 'PUBLICATION_DATE']
        read_only_fields = ['id', 'PUBLICATION_DATE']


class LectureWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LECTURES
        fields = ['id', 'NAME', 'VIDEO', 'ADDITIONAL_FILES', 'course']
        read_only_fields = ['id', 'course']


# ----------------------------------------------------------------------------- chat
@extend_schema_field(serializers.DictField(allow_null=True))
class _SenderField(serializers.Field):
    """Generic sender (student or instructor) rendered with the matching public serializer."""

    def to_representation(self, sender):
        if sender is None:
            return None
        return public_user_serializer(sender)(sender, context=self.context).data


class PeerChatMessageSerializer(serializers.ModelSerializer):
    sender = _SenderField(read_only=True)
    sender_cat = serializers.CharField(read_only=True)

    class Meta:
        model = PeerChat
        fields = ['id', 'message', 'sender', 'sender_cat', 'TimeStamp']
        read_only_fields = ['id', 'sender', 'sender_cat', 'TimeStamp']


class PeerConversationSerializer(serializers.Serializer):
    partner = serializers.SerializerMethodField()
    instructorName = serializers.CharField()
    studentName = serializers.CharField()
    last = PeerChatMessageSerializer(allow_null=True)
    url = serializers.SerializerMethodField()

    @extend_schema_field(serializers.DictField())
    def get_partner(self, conv):
        partner = conv['partner']
        return public_user_serializer(partner)(partner, context=self.context).data

    @extend_schema_field(serializers.URLField())
    def get_url(self, conv):
        from django.urls import reverse
        path = reverse('api:peer-chat-room', args=[conv['instructorName'], conv['studentName']])
        request = self.context.get('request')
        return request.build_absolute_uri(path) if request else path
