"""
Everything a tutor manages: his courses and their lectures, who is enrolled, the block
list and the mail-all-learners action. Mounted under /api/v1/instructor/.
Ownership is enforced in get_queryset, so a foreign course id simply returns 404.
"""
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from HOME_AREA.APIs import deliver_email, course_queryset
from HOME_AREA.models import COURSES, LECTURES
from HOME_AREA.permissions import IsInstructor
from HOME_AREA.serializers import (CourseListSerializer, CourseDetailSerializer, CourseWriteSerializer,
                                   LectureWriteSerializer, MessageSerializer, DetailSerializer,
                                   StudentPublicSerializer)
from STUDENT.models import STUDENT, COURSE_LIST
from .models import INSTRUCTOR, BLOCK_LIST
from .Serializers import BlockHandlerSerializer, CourseLearnersSerializer, InstructorProfileSerializer

UPLOAD_PARSERS = [MultiPartParser, FormParser, JSONParser]


def learners_of(course):
    return STUDENT.objects.filter(id__in=COURSE_LIST.objects.filter(course=course).values('student'))


class InstructorCourseViewSet(viewsets.ModelViewSet):
    """CRUD on the tutor's own courses, drafts included.
    Create with multipart: COURSE_NAME, COVER_PHOTO, IsDraft."""
    permission_classes = [IsAuthenticated, IsInstructor]
    parser_classes = UPLOAD_PARSERS

    def get_queryset(self):
        return course_queryset().filter(instructor_id=self.request.user.id).order_by('IsDraft', '-PUBLICATION_DATE')

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        if self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseWriteSerializer

    def perform_create(self, serializer):
        # the owner is always the logged in tutor, never something posted by the client
        serializer.save(instructor=self.request.user)

    def perform_destroy(self, instance):
        # COURSE_LIST.course is on_delete=DO_NOTHING, so enrolments must go first
        COURSE_LIST.objects.filter(course=instance).delete()
        instance.delete()

    def _detail_response(self, course, http_status=status.HTTP_200_OK):
        course = course_queryset().get(pk=course.pk)
        return Response(CourseDetailSerializer(course, context=self.get_serializer_context()).data, status=http_status)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return self._detail_response(serializer.instance, status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self._detail_response(serializer.instance)

    @extend_schema(request=None, responses={200: CourseDetailSerializer})
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        course = self.get_object()
        course.IsDraft = False
        course.save(update_fields=['IsDraft'])
        return self._detail_response(course)

    @extend_schema(request=MessageSerializer, responses={202: DetailSerializer})
    @action(detail=True, methods=['post'])
    def notify(self, request, pk=None):
        """Email every learner enrolled in the course."""
        course = self.get_object()
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipients = list(learners_of(course).values_list('EMAIL', flat=True))
        sent = sum(deliver_email(email, serializer.validated_data['message']) for email in recipients)
        return Response({'detail': f'Message sent to {sent} of {len(recipients)} learners.'},
                        status=status.HTTP_202_ACCEPTED)

    @extend_schema(responses={200: StudentPublicSerializer(many=True)})
    @action(detail=True, methods=['get'])
    def learners(self, request, pk=None):
        course = self.get_object()
        return Response(StudentPublicSerializer(learners_of(course), many=True,
                                                context=self.get_serializer_context()).data)


class InstructorLectureViewSet(viewsets.ModelViewSet):
    """Lectures of one of the tutor's courses. Upload with multipart: NAME, VIDEO, ADDITIONAL_FILES."""
    permission_classes = [IsAuthenticated, IsInstructor]
    parser_classes = UPLOAD_PARSERS
    serializer_class = LectureWriteSerializer

    def get_course(self):
        return get_object_or_404(COURSES, pk=self.kwargs['course_pk'], instructor_id=self.request.user.id)

    def get_queryset(self):
        return LECTURES.objects.filter(course=self.get_course()).order_by('id')

    def perform_create(self, serializer):
        serializer.save(course=self.get_course())


class LearnersAPI(APIView):
    """Every learner enrolled in any of the tutor's courses, grouped by course."""
    permission_classes = [IsAuthenticated, IsInstructor]

    @extend_schema(responses={200: CourseLearnersSerializer(many=True)})
    def get(self, request):
        rows = [{'course': course, 'learners': learners_of(course)}
                for course in course_queryset().filter(instructor_id=request.user.id)]
        return Response(CourseLearnersSerializer(rows, many=True, context={'request': request}).data)


class BlockListAPI(APIView):
    """Learners this tutor blocked from all his courses. POST {USER_NAME} to block one."""
    permission_classes = [IsAuthenticated, IsInstructor]
    serializer_class = BlockHandlerSerializer

    @extend_schema(responses={200: StudentPublicSerializer(many=True)})
    def get(self, request):
        blocked = STUDENT.objects.filter(
            id__in=BLOCK_LIST.objects.filter(instructors_id=request.user.id).values('students'))
        return Response(StudentPublicSerializer(blocked, many=True, context={'request': request}).data)

    @extend_schema(request=BlockHandlerSerializer,
                   responses={201: StudentPublicSerializer, 200: StudentPublicSerializer})
    def post(self, request):
        serializer = BlockHandlerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = get_object_or_404(STUDENT, USER_NAME=serializer.validated_data['USER_NAME'])
        _, created = BLOCK_LIST.objects.get_or_create(students=student, instructors=request.user)
        return Response(StudentPublicSerializer(student, context={'request': request}).data,
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class BlockDetailAPI(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    @extend_schema(responses={204: None})
    def delete(self, request, username):
        deleted, _ = BLOCK_LIST.objects.filter(students__USER_NAME=username,
                                               instructors_id=request.user.id).delete()
        if not deleted:
            return Response({'detail': 'This learner is not blocked.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class InstructorProfileAPI(APIView):
    """Public page of a tutor with his published courses."""
    permission_classes = [AllowAny]

    @extend_schema(responses={200: InstructorProfileSerializer})
    def get(self, request, username):
        instructor = get_object_or_404(INSTRUCTOR, USER_NAME=username, Isactive=True)
        instructor.courses = course_queryset().filter(instructor=instructor, IsDraft=False)
        return Response(InstructorProfileSerializer(instructor, context={'request': request}).data)
