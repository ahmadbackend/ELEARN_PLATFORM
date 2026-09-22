"""Student-only serializers. The shared ones (profile, courses, reviews...) live in HOME_AREA.serializers."""
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from HOME_AREA.serializers import StudentPublicSerializer, CourseListSerializer


class AppealSerializer(serializers.Serializer):
    appeal = serializers.CharField(max_length=2000)


class StudentProfileSerializer(StudentPublicSerializer):
    """Public dashboard of a learner: profile, status and enrolled courses."""
    status = serializers.SerializerMethodField()
    courses = CourseListSerializer(many=True, read_only=True)

    class Meta(StudentPublicSerializer.Meta):
        fields = StudentPublicSerializer.Meta.fields + ['status', 'courses']
        read_only_fields = fields

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_status(self, student):
        from HOME_AREA.user_status import get_status
        return get_status(student)
