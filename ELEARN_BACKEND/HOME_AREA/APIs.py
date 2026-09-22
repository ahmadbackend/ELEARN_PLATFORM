"""
REST endpoints shared by every role: auth flows, the current user (`me/`), the public
course catalogue and the learner <-> tutor peer chat.
Role specific write endpoints live in STUDENT/APIs.py and INSTRUCTOR/APIs.py.
"""
import logging
from random import randint

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import logout
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import generics, status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from INSTRUCTOR.models import BLOCK_LIST
from STUDENT.models import COURSE_LIST
from .access import resolve_peer_pair, can_peer_chat, peer_conversations
from .authentication import issue_token, TOKEN_MAX_AGE
from .models import COURSES, REVIEWS, PeerChat
from .passwords import set_password
from .serializers import (
    USER_MODEL, CODE_MODEL,
    StudentRegisterSerializer, InstructorRegisterSerializer, LoginSerializer, ActivateSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, TokenResponseSerializer, DetailSerializer,
    StudentPrivateSerializer, private_user_serializer, StatusSerializer, MessageSerializer,
    CourseListSerializer, CourseDetailSerializer, LectureSerializer, ReviewSerializer,
    PeerChatMessageSerializer, PeerConversationSerializer, rating_summary,
)
from .tasks import send_email, CleanDatabase
from .user_status import get_status, set_status, clear_status

logger = logging.getLogger(__name__)

UPLOAD_PARSERS = [MultiPartParser, FormParser, JSONParser]
# messages a peer chat room opens with
PEER_HISTORY_LIMIT = 20


# ----------------------------------------------------------------------------- helpers
def deliver_email(target, message):
    """Send `message` to `target` without ever letting a mail failure turn into a 500.
    Returns whether the mail went out."""
    try:
        send_email(target, message)
        return True
    except Exception:
        logger.exception('could not send email to %s', target)
        return False


def broadcast(group, payload):
    """Push `payload` to a channels group so websocket clients see REST-posted messages.
    Silently skipped when no channel layer is reachable: the message is already saved."""
    try:
        layer = get_channel_layer()
        if layer is not None:
            async_to_sync(layer.group_send)(group, payload)
    except Exception:
        logger.warning('channel layer unavailable, message saved but not broadcast', exc_info=True)


def course_queryset():
    return COURSES.objects.select_related('instructor').annotate(
        lecture_count=Count('lectures', distinct=True),
        enrolled_count=Count('course_list', distinct=True),
    )


def viewer_flags(course, request):
    return CourseDetailSerializer(course, context={'request': request}).viewer_flags(course)


# ----------------------------------------------------------------------------- auth
class _RegisterAPI(generics.CreateAPIView):
    permission_classes = [AllowAny]
    parser_classes = UPLOAD_PARSERS
    throttle_scope = 'register'
    user_type = None

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        code = randint(100000, 999999)
        CODE_MODEL[self.user_type].objects.create(USER_VERIFIER=user, ACTIVATION_CODE=code, EMAIL=user.EMAIL)
        sent = deliver_email(
            user.EMAIL,
            f'congrats for registering with us kindly use your email and the following code '
            f'to complete the registration {code}')
        return Response({'detail': 'Account created. Activate it with the code sent to your email.',
                         'email_sent': sent, 'user': serializer.data}, status=status.HTTP_201_CREATED)


class RegisterStudentAPI(_RegisterAPI):
    serializer_class = StudentRegisterSerializer
    user_type = 'student'


class RegisterInstructorAPI(_RegisterAPI):
    serializer_class = InstructorRegisterSerializer
    user_type = 'instructor'


class LoginAPI(APIView):
    permission_classes = [AllowAny]
    throttle_scope = 'login'
    serializer_class = LoginSerializer

    @extend_schema(request=LoginSerializer, responses={200: TokenResponseSerializer})
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        user_type = serializer.validated_data['user_type']
        if not user.Isactive:
            return Response({'detail': 'Account not activated yet. Check your inbox or junk mail for the code.',
                             'Isactive': False}, status=status.HTTP_403_FORBIDDEN)
        # stateless on purpose: no session cookie is set, the SPA only ever sends the header
        CleanDatabase(user.EMAIL, CODE_MODEL[user_type])
        profile = private_user_serializer(user)(user, context={'request': request}).data
        return Response({'token': issue_token(user), 'expires_in': TOKEN_MAX_AGE, 'user': profile})


class LogoutAPI(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={200: DetailSerializer})
    def post(self, request):
        # tokens are stateless, so logging out is the client forgetting the token;
        # this only closes a django session if the caller happened to have one
        logout(request._request)
        return Response({'detail': 'Discard the token on the client; it stays valid until it expires.'})


class ActivateAPI(APIView):
    permission_classes = [AllowAny]
    throttle_scope = 'code'
    serializer_class = ActivateSerializer

    @extend_schema(request=ActivateSerializer, responses={200: DetailSerializer})
    def post(self, request):
        serializer = ActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        code_ok = CODE_MODEL[d['user_type']].objects.filter(
            EMAIL=d['EMAIL'], ACTIVATION_CODE=d['ACTIVATION_CODE']).exists()
        user = USER_MODEL[d['user_type']].objects.filter(EMAIL=d['EMAIL']).first()
        if not code_ok or user is None:
            return Response({'detail': 'Invalid activation code or email.'}, status=status.HTTP_400_BAD_REQUEST)
        user.Isactive = True
        user.save(update_fields=['Isactive'])
        CleanDatabase(user.EMAIL, CODE_MODEL[d['user_type']])
        return Response({'detail': 'Account activated. You can log in now.'})


class ForgotPasswordAPI(APIView):
    permission_classes = [AllowAny]
    throttle_scope = 'code'
    serializer_class = ForgotPasswordSerializer

    @extend_schema(request=ForgotPasswordSerializer, responses={202: DetailSerializer})
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        # the answer is the same whether or not the address is registered, so this
        # endpoint cannot be used to find out who has an account here
        answer = {'detail': 'If that address has an account, a reset code is on its way.',
                  'email_sent': True}
        user = USER_MODEL[d['user_type']].objects.filter(EMAIL=d['EMAIL']).first()
        if user is None:
            return Response(answer, status=status.HTTP_202_ACCEPTED)
        code = randint(100000, 999999)
        CODE_MODEL[d['user_type']].objects.create(USER_VERIFIER=user, ACTIVATION_CODE=code, EMAIL=user.EMAIL)
        deliver_email(
            user.EMAIL,
            f'this code was sent based on your request to restore the login credential. '
            f'Ignore if you did not send it: {code}')
        return Response(answer, status=status.HTTP_202_ACCEPTED)


class ResetPasswordAPI(APIView):
    permission_classes = [AllowAny]
    throttle_scope = 'code'
    serializer_class = ResetPasswordSerializer

    @extend_schema(request=ResetPasswordSerializer, responses={200: DetailSerializer})
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        code_ok = CODE_MODEL[d['user_type']].objects.filter(
            EMAIL=d['EMAIL'], ACTIVATION_CODE=d['ACTIVATION_CODE']).exists()
        user = USER_MODEL[d['user_type']].objects.filter(EMAIL=d['EMAIL']).first()
        if not code_ok or user is None:
            return Response({'detail': 'Invalid activation code or email.'}, status=status.HTTP_400_BAD_REQUEST)
        set_password(user, d['PASSWORD'])
        CleanDatabase(user.EMAIL, CODE_MODEL[d['user_type']])
        deliver_email(user.EMAIL, 'you have reset your password successfully. If it was not you '
                                  'please go to your account and reset it immediately')
        return Response({'detail': 'Password updated. Log in with the new password.'})


# ----------------------------------------------------------------------------- me
class MeAPI(generics.RetrieveUpdateDestroyAPIView):
    """Profile of the logged in student or instructor."""
    permission_classes = [IsAuthenticated]
    parser_classes = UPLOAD_PARSERS

    def get_serializer_class(self):
        user = getattr(self.request, 'user', None)
        if getattr(user, 'user_cat', None):
            return private_user_serializer(user)
        return StudentPrivateSerializer  # schema generation only

    def get_object(self):
        return self.request.user

    def perform_destroy(self, instance):
        clear_status(instance)
        logout(self.request._request)
        # COURSE_LIST / BLOCK_LIST point at users with on_delete=DO_NOTHING: clear them by hand
        if instance.user_cat == 'student':
            COURSE_LIST.objects.filter(student=instance).delete()
            BLOCK_LIST.objects.filter(students=instance).delete()
        else:
            COURSE_LIST.objects.filter(course__instructor=instance).delete()
            BLOCK_LIST.objects.filter(instructors=instance).delete()
        instance.delete()


class MeStatusAPI(APIView):
    """The free-text status shown on the dashboard (stored in the cache for 30 days)."""
    permission_classes = [IsAuthenticated]
    serializer_class = StatusSerializer

    @extend_schema(responses={200: StatusSerializer})
    def get(self, request):
        return Response({'status': get_status(request.user)})

    @extend_schema(request=StatusSerializer, responses={200: StatusSerializer})
    def put(self, request):
        serializer = StatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_status(request.user, serializer.validated_data['status'])
        return Response(serializer.validated_data)

    @extend_schema(responses={204: None})
    def delete(self, request):
        clear_status(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeCoursesAPI(generics.ListAPIView):
    """Student: enrolled courses. Instructor: own courses, drafts included."""
    permission_classes = [IsAuthenticated]
    serializer_class = CourseListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = course_queryset()
        if getattr(user, 'user_cat', None) == 'instructor':
            return qs.filter(instructor_id=user.id).order_by('IsDraft', '-PUBLICATION_DATE')
        if getattr(user, 'user_cat', None) == 'student':
            enrolled = COURSE_LIST.objects.filter(student_id=user.id).values('course')
            return qs.filter(id__in=enrolled).order_by('-PUBLICATION_DATE')
        return qs.none()


# ----------------------------------------------------------------------------- courses
@extend_schema_view(list=extend_schema(parameters=[
    OpenApiParameter('instructor', str, description='filter by instructor USER_NAME'),
    OpenApiParameter('search', str, description='match on course or instructor name'),
]))
class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """Public catalogue. Drafts are hidden from everybody but their owner."""
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['COURSE_NAME', 'instructor__USER_NAME']
    ordering_fields = ['PUBLICATION_DATE', 'COURSE_NAME']
    ordering = ['-PUBLICATION_DATE']

    def get_queryset(self):
        user = self.request.user
        qs = course_queryset()
        if getattr(user, 'user_cat', None) == 'instructor':
            qs = qs.filter(Q(IsDraft=False) | Q(instructor_id=user.id))
        else:
            qs = qs.filter(IsDraft=False)
        instructor = self.request.query_params.get('instructor')
        if instructor:
            qs = qs.filter(instructor__USER_NAME=instructor)
        return qs

    def get_serializer_class(self):
        return CourseDetailSerializer if self.action == 'retrieve' else CourseListSerializer

    @extend_schema(responses={200: LectureSerializer(many=True)})
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def lectures(self, request, pk=None):
        course = self.get_object()
        if not viewer_flags(course, request)['can_watch']:
            raise PermissionDenied('Enroll in this course to watch its lectures.')
        serializer = LectureSerializer(course.lectures.all(), many=True,
                                       context={'request': request, 'can_watch': True})
        return Response(serializer.data)

    @extend_schema(responses={200: ReviewSerializer(many=True)})
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        course = self.get_object()
        reviews = REVIEWS.objects.filter(reviews=course).select_related('USER_NAME')
        page = self.paginate_queryset(reviews)
        serializer = ReviewSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['get'])
    def ratings(self, request, pk=None):
        return Response(rating_summary(self.get_object()))


# ----------------------------------------------------------------------------- peer chat
class PeerChatListAPI(APIView):
    """Inbox: every tutor/learner the current user may talk to, most recently active first."""
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: PeerConversationSerializer(many=True)})
    def get(self, request):
        data = PeerConversationSerializer(peer_conversations(request.user), many=True,
                                          context={'request': request}).data
        return Response(data)


class PeerChatRoomAPI(APIView):
    """History of one learner <-> tutor conversation, or send a message into it."""
    permission_classes = [IsAuthenticated]
    serializer_class = PeerChatMessageSerializer

    def get_pair(self, request, instructorName, studentName):
        pair = resolve_peer_pair(request.user, instructorName, studentName)
        if pair is None:
            raise PermissionDenied('You can only chat with a tutor whose course you are enrolled in.')
        return pair

    @extend_schema(operation_id='peer_chat_room_messages', parameters=[
        OpenApiParameter('limit', int, description='how many of the most recent messages (default 20, max 200)'),
        OpenApiParameter('after', int, description='only messages with id greater than this (polling)'),
    ], responses={200: PeerChatMessageSerializer(many=True)})
    def get(self, request, instructorName, studentName):
        instructor, student = self.get_pair(request, instructorName, studentName)
        chats = PeerChat.objects.filter(instructor=instructor, student=student)
        after = request.query_params.get('after')
        if after and after.isdigit():
            chats = chats.filter(id__gt=int(after))
        # the SPA opens the room with the last N messages, oldest first
        limit = request.query_params.get('limit')
        limit = min(int(limit), 200) if limit and limit.isdigit() and int(limit) > 0 else PEER_HISTORY_LIMIT
        recent = list(chats.order_by('-TimeStamp', '-id')[:limit])
        recent.reverse()
        return Response(PeerChatMessageSerializer(recent, many=True, context={'request': request}).data)

    @extend_schema(operation_id='peer_chat_room_send', request=MessageSerializer,
                   responses={201: PeerChatMessageSerializer})
    def post(self, request, instructorName, studentName):
        instructor, student = self.get_pair(request, instructorName, studentName)
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # re-checked on every message so a drop or a block takes effect immediately
        if not can_peer_chat(student, instructor):
            raise PermissionDenied('This conversation is no longer available.')
        chat = PeerChat.objects.create(
            student=student, instructor=instructor, message=serializer.validated_data['message'][:1000],
            content_type=ContentType.objects.get_for_model(request.user.__class__), object_id=request.user.id)
        broadcast(PeerChat.group_name(instructor, student), {
            'type': 'peer.message', 'message': chat.message, 'userName': request.user.USER_NAME,
            'userCat': request.user.user_cat, 'timeStamp': chat.TimeStamp.isoformat()})
        return Response(PeerChatMessageSerializer(chat, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)
