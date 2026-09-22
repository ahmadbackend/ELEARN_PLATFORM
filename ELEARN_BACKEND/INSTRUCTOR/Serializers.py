"""Instructor-only serializers. The shared ones (courses, lectures, profile...) live in HOME_AREA.serializers."""
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from HOME_AREA.serializers import (InstructorPublicSerializer, StudentPublicSerializer,
                                   CourseListSerializer)


class BlockHandlerSerializer(serializers.Serializer):
    USER_NAME = serializers.CharField(max_length=50)


class CourseLearnersSerializer(serializers.Serializer):
    course = CourseListSerializer(read_only=True)
    learners = StudentPublicSerializer(many=True, read_only=True)


class InstructorProfileSerializer(InstructorPublicSerializer):
    """Public page of a tutor: profile, status and published courses."""
    status = serializers.SerializerMethodField()
    courses = CourseListSerializer(many=True, read_only=True)

    class Meta(InstructorPublicSerializer.Meta):
        fields = InstructorPublicSerializer.Meta.fields + ['status', 'courses']
        read_only_fields = fields

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_status(self, instructor):
        from HOME_AREA.user_status import get_status
        return get_status(instructor)
