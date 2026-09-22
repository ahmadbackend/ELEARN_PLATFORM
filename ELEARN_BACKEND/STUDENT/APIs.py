"""
Endpoints a learner uses on a course: enrol/drop, his own review and rating, and the
appeal he can send when a tutor blocked him. Mounted under /api/v1/student/.
"""
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from HOME_AREA.APIs import deliver_email, course_queryset
from HOME_AREA.models import COURSES, REVIEWS, Rating
from HOME_AREA.permissions import IsStudent
from HOME_AREA.serializers import ReviewSerializer, RatingSerializer, DetailSerializer
from INSTRUCTOR.models import BLOCK_LIST
from .models import STUDENT, COURSE_LIST
from .serializers import AppealSerializer, StudentProfileSerializer


def published_course(pk):
    return get_object_or_404(COURSES.objects.select_related('instructor'), pk=pk, IsDraft=False)


def is_blocked(student, course):
    return BLOCK_LIST.objects.filter(students=student, instructors=course.instructor).exists()


class EnrollmentAPI(APIView):
    """POST to enrol in a course, DELETE to drop it."""
    permission_classes = [IsAuthenticated, IsStudent]

    @extend_schema(request=None, responses={201: DetailSerializer, 200: DetailSerializer})
    def post(self, request, pk):
        course = published_course(pk)
        if is_blocked(request.user, course):
            raise PermissionDenied('The instructor of this course has blocked you. Send an appeal instead.')
        _, created = COURSE_LIST.objects.get_or_create(course=course, student=request.user)
        if not created:
            return Response({'detail': 'Already enrolled.'})
        return Response({'detail': f'Enrolled in {course.COURSE_NAME}.'}, status=status.HTTP_201_CREATED)

    @extend_schema(responses={204: None})
    def delete(self, request, pk):
        course = get_object_or_404(COURSES, pk=pk)
        deleted, _ = COURSE_LIST.objects.filter(course=course, student=request.user).delete()
        if not deleted:
            return Response({'detail': 'You are not enrolled in this course.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class _OwnCourseItemAPI(APIView):
    """GET / PUT (upsert) / DELETE of the single item a learner owns on a course."""
    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = None
    model = None
    # how the model names the course and the student columns
    course_field = None
    student_field = None

    def lookup(self, request, pk):
        course = published_course(pk)
        return course, {self.course_field: course, self.student_field: request.user}

    def get(self, request, pk):
        _, key = self.lookup(request, pk)
        obj = self.model.objects.filter(**key).first()
        if obj is None:
            return Response({'detail': 'Nothing submitted yet.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.serializer_class(obj, context={'request': request}).data)

    def put(self, request, pk):
        _, key = self.lookup(request, pk)
        if not COURSE_LIST.objects.filter(course=key[self.course_field], student=request.user).exists():
            raise PermissionDenied('Enroll in the course first.')
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj, created = self.model.objects.update_or_create(**key, defaults=serializer.validated_data)
        return Response(self.serializer_class(obj, context={'request': request}).data,
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def delete(self, request, pk):
        _, key = self.lookup(request, pk)
        deleted, _ = self.model.objects.filter(**key).delete()
        if not deleted:
            return Response({'detail': 'Nothing to delete.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyReviewAPI(_OwnCourseItemAPI):
    """The learner's review of a course (one per learner, PUT creates or replaces it)."""
    serializer_class = ReviewSerializer
    model = REVIEWS
    course_field = 'reviews'
    student_field = 'USER_NAME'


class MyRatingAPI(_OwnCourseItemAPI):
    """The learner's 1-5 rating of a course (one per learner, PUT creates or replaces it)."""
    serializer_class = RatingSerializer
    model = Rating
    course_field = 'course'
    student_field = 'user'


class AppealAPI(APIView):
    """A blocked learner asks the course's instructor to lift the block (sent by email)."""
    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = AppealSerializer

    @extend_schema(request=AppealSerializer, responses={202: DetailSerializer})
    def post(self, request, pk):
        course = published_course(pk)
        if not is_blocked(request.user, course):
            return Response({'detail': 'You are not blocked by this instructor.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = AppealSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appeal = serializer.validated_data['appeal']
        sent = deliver_email(course.instructor.EMAIL, f'Appeal from {request.user.USER_NAME}: {appeal}')
        deliver_email(request.user.EMAIL, f'your message was sent successfully and here is a copy of it: {appeal}')
        return Response({'detail': 'Appeal sent to the instructor.', 'email_sent': sent},
                        status=status.HTTP_202_ACCEPTED)


class StudentProfileAPI(APIView):
    """What peers and tutors see about a learner (the MVT "Dashboard/<username>" page)."""
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: StudentProfileSerializer})
    def get(self, request, username):
        student = get_object_or_404(STUDENT, USER_NAME=username, Isactive=True)
        enrolled = COURSE_LIST.objects.filter(student=student).values('course')
        student.courses = course_queryset().filter(id__in=enrolled, IsDraft=False)
        return Response(StudentProfileSerializer(student, context={'request': request}).data)
