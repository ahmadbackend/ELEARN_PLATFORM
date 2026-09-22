# single place for the rule that decides who may open a peer-to-peer chat.
# used by the http view and the websocket consumer so they can never disagree
from HOME_AREA.models import PeerChat
from INSTRUCTOR.models import INSTRUCTOR, BLOCK_LIST
from STUDENT.models import STUDENT, COURSE_LIST


def can_peer_chat(student, instructor):
    # learner must be enrolled in at least one of the tutor's courses
    enrolled = COURSE_LIST.objects.filter(student=student, course__instructor=instructor).exists()
    if not enrolled:
        return False
    # and must not be blocked by that tutor
    return not BLOCK_LIST.objects.filter(students=student, instructors=instructor).exists()


def resolve_peer_pair(user, instructorName, studentName):
    """
    Returns (instructor, student) when `user` is one side of the pair and the pair is allowed to chat,
    otherwise None. Prevents a logged in user from opening somebody else's conversation.
    """
    if not hasattr(user, 'user_cat'):
        return None
    try:
        instructor = INSTRUCTOR.objects.get(USER_NAME=instructorName)
        student = STUDENT.objects.get(USER_NAME=studentName)
    except (INSTRUCTOR.DoesNotExist, STUDENT.DoesNotExist):
        return None

    if user.user_cat == 'student' and user.id != student.id:
        return None
    if user.user_cat == 'instructor' and user.id != instructor.id:
        return None

    if not can_peer_chat(student, instructor):
        return None
    return instructor, student


def peer_conversations(user):
    """
    Every tutor/learner `user` may talk to, with the last message if any, most recently
    active first. Shared by the MVT inbox page and the REST endpoint.
    """
    conversations = []
    if user.user_cat == 'student':
        instructor_ids = COURSE_LIST.objects.filter(student=user).values_list('course__instructor', flat=True).distinct()
        for instructor in INSTRUCTOR.objects.filter(id__in=instructor_ids):
            if not can_peer_chat(user, instructor):
                continue
            last = PeerChat.objects.filter(instructor=instructor, student=user).last()
            conversations.append({'partner': instructor, 'instructorName': instructor.USER_NAME,
                                  'studentName': user.USER_NAME, 'last': last})
    else:
        student_ids = COURSE_LIST.objects.filter(course__instructor=user).values_list('student', flat=True).distinct()
        for student in STUDENT.objects.filter(id__in=student_ids):
            if not can_peer_chat(student, user):
                continue
            last = PeerChat.objects.filter(instructor=user, student=student).last()
            conversations.append({'partner': student, 'instructorName': user.USER_NAME,
                                  'studentName': student.USER_NAME, 'last': last})

    conversations.sort(key=lambda c: (1, c['last'].TimeStamp) if c['last'] else (0, 0), reverse=True)
    return conversations
