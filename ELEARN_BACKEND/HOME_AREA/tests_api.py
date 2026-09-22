"""
Tests for the /api/v1/ surface. Run with:  python manage.py test HOME_AREA.tests_api
Email sending and the channel layer are stubbed so no SMTP / broker is needed.
"""
import tempfile
from io import BytesIO
from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from HOME_AREA.models import COURSES, LECTURES, PeerChat, REVIEWS
from HOME_AREA.passwords import check_user_password, hash_password, is_hashed
from INSTRUCTOR.models import INSTRUCTOR, BLOCK_LIST, CODE_GENERATOR_INSTR
from STUDENT.models import STUDENT, COURSE_LIST, CODE_GENERATOR

TEST_SETTINGS = dict(
    MEDIA_ROOT=tempfile.mkdtemp(),
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    CHANNEL_LAYERS={'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}},
)


# the raw password every fixture user is created with
PASSWORD = 'password1'


def png(name='pic.png'):
    # a real image: the serializer's ImageField validates uploads with Pillow
    from PIL import Image
    buf = BytesIO()
    Image.new('RGB', (1, 1)).save(buf, 'PNG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')


@override_settings(**TEST_SETTINGS)
class ApiTestCase(APITestCase):
    def setUp(self):
        # the auth endpoints are rate limited per IP and the throttle history lives in
        # the cache, so each test starts from an empty one
        cache.clear()
        self.tutor = INSTRUCTOR.objects.create(FIRST_NAME='Tina', LAST_NAME='Tutor', USER_NAME='tutor1',
                                               EMAIL='tutor1@example.com', PHONE='1000001', PASSWORD=hash_password(PASSWORD),
                                               PICTURE=png(), Isactive=True)
        self.learner = STUDENT.objects.create(FIRST_NAME='Lee', LAST_NAME='Learner', USER_NAME='learner1',
                                              EMAIL='learner1@example.com', PHONE='2000001', PASSWORD=hash_password(PASSWORD),
                                              Isactive=True)
        self.stranger = STUDENT.objects.create(FIRST_NAME='Sam', LAST_NAME='Stranger', USER_NAME='learner2',
                                               EMAIL='learner2@example.com', PHONE='2000002', PASSWORD=hash_password(PASSWORD),
                                               Isactive=True)
        self.course = COURSES.objects.create(COURSE_NAME='Django 101', COVER_PHOTO=png(), instructor=self.tutor)
        self.draft = COURSES.objects.create(COURSE_NAME='Secret draft', COVER_PHOTO=png(), instructor=self.tutor,
                                            IsDraft=True)
        self.lecture = LECTURES.objects.create(NAME='Intro', course=self.course)
        COURSE_LIST.objects.create(student=self.learner, course=self.course)

    def token_for(self, user):
        from HOME_AREA.authentication import issue_token
        return issue_token(user)

    def auth(self, user):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token_for(user))

    def url(self, name, *args):
        return reverse('api:' + name, args=args)


class AuthTests(ApiTestCase):
    def test_login_returns_token_and_profile(self):
        r = self.client.post(self.url('login'), {'user_type': 'student', 'EMAIL': 'learner1@example.com',
                                                 'PASSWORD': 'password1'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertIn('token', r.data)
        self.assertEqual(r.data['user']['USER_NAME'], 'learner1')
        self.assertNotIn('PASSWORD', r.data['user'])

    def test_login_rejects_wrong_password_and_wrong_role(self):
        bad = self.client.post(self.url('login'), {'user_type': 'student', 'EMAIL': 'learner1@example.com',
                                                   'PASSWORD': 'nope'}, format='json')
        self.assertEqual(bad.status_code, 400)
        # a learner's credentials must not open an instructor session
        role = self.client.post(self.url('login'), {'user_type': 'instructor', 'EMAIL': 'learner1@example.com',
                                                    'PASSWORD': 'password1'}, format='json')
        self.assertEqual(role.status_code, 400)

    def test_inactive_account_cannot_login(self):
        self.learner.Isactive = False
        self.learner.save()
        r = self.client.post(self.url('login'), {'user_type': 'student', 'EMAIL': 'learner1@example.com',
                                                 'PASSWORD': 'password1'}, format='json')
        self.assertEqual(r.status_code, 403)
        self.assertIs(r.data['Isactive'], False)

    def test_passwords_are_stored_hashed(self):
        for user in (self.learner, self.tutor):
            self.assertNotEqual(user.PASSWORD, PASSWORD)
            self.assertTrue(is_hashed(user.PASSWORD))
            self.assertTrue(check_user_password(user, PASSWORD))

    @patch('HOME_AREA.APIs.send_email')
    def test_registration_stores_a_hash(self, send_email):
        r = self.client.post(self.url('register-student'), {
            'FIRST_NAME': 'Hash', 'LAST_NAME': 'Ed', 'USER_NAME': 'hashed', 'EMAIL': 'hashed@example.com',
            'PHONE': '3000003', 'PASSWORD': 'secret123'}, format='multipart')
        self.assertEqual(r.status_code, 201, r.data)
        student = STUDENT.objects.get(USER_NAME='hashed')
        self.assertNotEqual(student.PASSWORD, 'secret123')
        self.assertTrue(check_user_password(student, 'secret123'))

    def test_forgot_password_does_not_reveal_whether_the_email_exists(self):
        known = self.client.post(self.url('password-forgot'),
                                 {'user_type': 'student', 'EMAIL': 'learner1@example.com'}, format='json')
        unknown = self.client.post(self.url('password-forgot'),
                                   {'user_type': 'student', 'EMAIL': 'nobody@example.com'}, format='json')
        self.assertEqual(known.status_code, unknown.status_code)
        self.assertEqual(known.data, unknown.data)

    def test_login_sets_no_cookie(self):
        r = self.client.post(self.url('login'), {'user_type': 'student', 'EMAIL': 'learner1@example.com',
                                                 'PASSWORD': 'password1'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('sessionid', r.cookies)

    def test_token_is_a_readable_jwt(self):
        import base64
        import json
        token = self.token_for(self.learner)
        header, payload, _ = token.split('.')
        decode = lambda part: json.loads(base64.urlsafe_b64decode(part + '=' * (-len(part) % 4)))
        self.assertEqual(decode(header)['alg'], 'HS256')
        claims = decode(payload)
        self.assertEqual(claims['cat'], 'student')
        self.assertEqual(claims['sub'], self.learner.id)
        self.assertGreater(claims['exp'], claims['iat'])
        # tampering with the payload breaks the signature
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + header + '.' + payload[:-2] + 'xx.' + token.split('.')[2])
        self.assertEqual(self.client.get(self.url('me')).status_code, 401)

    def test_token_authenticates_and_password_reset_invalidates_it(self):
        self.assertEqual(self.client.get(self.url('me')).status_code, 401)
        self.auth(self.learner)
        r = self.client.get(self.url('me'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['user_cat'], 'student')
        self.learner.PASSWORD = hash_password('password2')
        self.learner.save()
        self.assertEqual(self.client.get(self.url('me')).status_code, 401)

    @patch('HOME_AREA.APIs.send_email')
    def test_register_then_activate_student(self, send_email):
        r = self.client.post(self.url('register-student'), {
            'FIRST_NAME': 'New', 'LAST_NAME': 'Kid', 'USER_NAME': 'newkid', 'EMAIL': 'new@example.com',
            'PHONE': '3000001', 'PASSWORD': 'secret123'}, format='multipart')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(r.data['email_sent'])
        send_email.assert_called_once()
        student = STUDENT.objects.get(USER_NAME='newkid')
        self.assertFalse(student.Isactive)
        code = CODE_GENERATOR.objects.get(EMAIL='new@example.com').ACTIVATION_CODE

        r = self.client.post(self.url('activate'), {'user_type': 'student', 'EMAIL': 'new@example.com',
                                                    'ACTIVATION_CODE': code}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        student.refresh_from_db()
        self.assertTrue(student.Isactive)
        self.assertFalse(CODE_GENERATOR.objects.filter(EMAIL='new@example.com').exists())

    @patch('HOME_AREA.APIs.send_email')
    def test_register_instructor_requires_picture(self, send_email):
        r = self.client.post(self.url('register-instructor'), {
            'FIRST_NAME': 'No', 'LAST_NAME': 'Pic', 'USER_NAME': 'nopic', 'EMAIL': 'nopic@example.com',
            'PHONE': '3000002', 'PASSWORD': 'secret123'}, format='multipart')
        self.assertEqual(r.status_code, 400)
        self.assertIn('PICTURE', r.data)

    @patch('HOME_AREA.APIs.send_email')
    def test_forgot_and_reset_password(self, send_email):
        r = self.client.post(self.url('password-forgot'), {'user_type': 'instructor', 'EMAIL': 'tutor1@example.com'},
                             format='json')
        self.assertEqual(r.status_code, 202, r.data)
        code = CODE_GENERATOR_INSTR.objects.get(EMAIL='tutor1@example.com').ACTIVATION_CODE
        r = self.client.post(self.url('password-reset'), {
            'user_type': 'instructor', 'EMAIL': 'tutor1@example.com', 'ACTIVATION_CODE': code,
            'PASSWORD': 'newpass99', 'CONFIRM_PASSWORD': 'newpass99'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.tutor.refresh_from_db()
        self.assertNotEqual(self.tutor.PASSWORD, 'newpass99')
        self.assertTrue(is_hashed(self.tutor.PASSWORD))
        self.assertTrue(check_user_password(self.tutor, 'newpass99'))


class MeTests(ApiTestCase):
    def test_update_profile_and_status(self):
        self.auth(self.learner)
        r = self.client.patch(self.url('me'), {'FIRST_NAME': 'Leah'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['FIRST_NAME'], 'Leah')

        r = self.client.put(self.url('me-status'), {'status': 'learning hard'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.get(self.url('me-status')).data['status'], 'learning hard')
        # visible on the public profile too
        r = self.client.get(self.url('student-profile', 'learner1'))
        self.assertEqual(r.data['status'], 'learning hard')
        self.assertEqual([c['id'] for c in r.data['courses']], [self.course.id])

    def test_me_courses_per_role(self):
        self.auth(self.learner)
        ids = [c['id'] for c in self.client.get(self.url('me-courses')).data['results']]
        self.assertEqual(ids, [self.course.id])
        self.auth(self.tutor)
        ids = {c['id'] for c in self.client.get(self.url('me-courses')).data['results']}
        self.assertEqual(ids, {self.course.id, self.draft.id})  # owner sees drafts


class CourseCatalogueTests(ApiTestCase):
    def test_list_is_public_and_hides_drafts(self):
        r = self.client.get(self.url('course-list'))
        self.assertEqual(r.status_code, 200)
        names = [c['COURSE_NAME'] for c in r.data['results']]
        self.assertEqual(names, ['Django 101'])
        self.assertEqual(r.data['results'][0]['enrolled_count'], 1)
        self.assertEqual(r.data['results'][0]['lecture_count'], 1)
        self.assertEqual(self.client.get(self.url('course-detail', self.draft.id)).status_code, 404)

    def test_detail_gates_media_behind_enrolment(self):
        r = self.client.get(self.url('course-detail', self.course.id))
        self.assertEqual(r.data['viewer']['can_watch'], False)
        self.assertEqual(r.data['lectures'][0]['NAME'], 'Intro')
        self.assertIsNone(r.data['lectures'][0]['VIDEO'])

        self.auth(self.stranger)
        self.assertEqual(self.client.get(self.url('course-lectures', self.course.id)).status_code, 403)

        self.auth(self.learner)
        r = self.client.get(self.url('course-detail', self.course.id))
        self.assertTrue(r.data['viewer']['enrolled'])
        self.assertTrue(r.data['viewer']['can_watch'])
        self.assertEqual(self.client.get(self.url('course-lectures', self.course.id)).status_code, 200)

    def test_reviews_and_ratings(self):
        self.auth(self.learner)
        r = self.client.put(self.url('student-review', self.course.id), {'OPINION': 'great'}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        r = self.client.put(self.url('student-review', self.course.id), {'OPINION': 'even better'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(REVIEWS.objects.filter(USER_NAME=self.learner).count(), 1)

        self.assertEqual(self.client.put(self.url('student-rating', self.course.id), {'RATING': 5},
                                         format='json').status_code, 201)
        summary = self.client.get(self.url('course-ratings', self.course.id)).data
        self.assertEqual(summary['average'], 5)
        self.assertEqual(summary['breakdown']['5'], 1)

        reviews = self.client.get(self.url('course-reviews', self.course.id)).data['results']
        self.assertEqual(reviews[0]['OPINION'], 'even better')
        self.assertEqual(reviews[0]['USER_NAME']['USER_NAME'], 'learner1')

        # not enrolled -> cannot review
        self.auth(self.stranger)
        self.assertEqual(self.client.put(self.url('student-review', self.course.id), {'OPINION': 'x'},
                                         format='json').status_code, 403)


class EnrolmentTests(ApiTestCase):
    def test_enroll_and_drop(self):
        self.auth(self.stranger)
        r = self.client.post(self.url('student-enroll', self.course.id))
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(self.client.post(self.url('student-enroll', self.course.id)).status_code, 200)
        self.assertEqual(self.client.delete(self.url('student-enroll', self.course.id)).status_code, 204)
        self.assertFalse(COURSE_LIST.objects.filter(student=self.stranger, course=self.course).exists())

    def test_blocked_learner_cannot_enroll_but_can_appeal(self):
        BLOCK_LIST.objects.create(students=self.stranger, instructors=self.tutor)
        self.auth(self.stranger)
        self.assertEqual(self.client.post(self.url('student-enroll', self.course.id)).status_code, 403)
        with patch('HOME_AREA.APIs.send_email') as send_email:
            r = self.client.post(self.url('student-appeal', self.course.id), {'appeal': 'sorry'}, format='json')
        self.assertEqual(r.status_code, 202, r.data)
        self.assertEqual(send_email.call_count, 2)

    def test_instructor_cannot_enroll(self):
        self.auth(self.tutor)
        self.assertEqual(self.client.post(self.url('student-enroll', self.course.id)).status_code, 403)


class InstructorTests(ApiTestCase):
    def test_course_lifecycle(self):
        self.auth(self.tutor)
        r = self.client.post(self.url('instructor-course-list'),
                             {'COURSE_NAME': 'New course', 'COVER_PHOTO': png('cover.png'), 'IsDraft': True},
                             format='multipart')
        self.assertEqual(r.status_code, 201, r.data)
        course_id = r.data['id']
        self.assertEqual(COURSES.objects.get(pk=course_id).instructor, self.tutor)
        self.assertTrue(r.data['viewer']['is_owner'])

        # add a lecture, then publish
        r = self.client.post(self.url('instructor-lecture-list', course_id), {'NAME': 'Lecture 1'},
                             format='multipart')
        self.assertEqual(r.status_code, 201, r.data)
        r = self.client.post(self.url('instructor-course-publish', course_id))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.data['IsDraft'])
        self.assertEqual(r.data['lecture_count'], 1)

        r = self.client.patch(self.url('instructor-course-detail', course_id), {'COURSE_NAME': 'Renamed'},
                              format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['COURSE_NAME'], 'Renamed')
        COURSE_LIST.objects.create(student=self.stranger, course_id=course_id)
        self.assertEqual(self.client.delete(self.url('instructor-course-detail', course_id)).status_code, 204)
        self.assertFalse(COURSE_LIST.objects.filter(course_id=course_id).exists())

    def test_cannot_touch_another_tutors_course(self):
        other = INSTRUCTOR.objects.create(FIRST_NAME='O', LAST_NAME='T', USER_NAME='tutor2',
                                          EMAIL='tutor2@example.com', PHONE='1000002', PASSWORD=hash_password('password1'),
                                          PICTURE=png(), Isactive=True)
        self.auth(other)
        self.assertEqual(self.client.get(self.url('instructor-course-detail', self.course.id)).status_code, 404)
        self.assertEqual(self.client.post(self.url('instructor-lecture-list', self.course.id), {'NAME': 'x'},
                                          format='multipart').status_code, 404)
        self.auth(self.learner)
        self.assertEqual(self.client.get(self.url('instructor-course-list')).status_code, 403)

    def test_learners_and_blocks(self):
        self.auth(self.tutor)
        r = self.client.get(self.url('instructor-learners'))
        by_course = {row['course']['COURSE_NAME']: [s['USER_NAME'] for s in row['learners']] for row in r.data}
        self.assertEqual(by_course['Django 101'], ['learner1'])

        r = self.client.post(self.url('instructor-blocks'), {'USER_NAME': 'learner1'}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(BLOCK_LIST.objects.filter(students=self.learner, instructors=self.tutor).exists())
        self.assertEqual([s['USER_NAME'] for s in self.client.get(self.url('instructor-blocks')).data], ['learner1'])
        self.assertEqual(self.client.delete(self.url('instructor-block-detail', 'learner1')).status_code, 204)
        self.assertEqual(self.client.delete(self.url('instructor-block-detail', 'learner1')).status_code, 404)

    @patch('HOME_AREA.APIs.send_email')
    def test_notify_learners(self, send_email):
        self.auth(self.tutor)
        r = self.client.post(self.url('instructor-course-notify', self.course.id), {'message': 'new lecture!'},
                             format='json')
        self.assertEqual(r.status_code, 202, r.data)
        send_email.assert_called_once_with('learner1@example.com', 'new lecture!')


class ChatTests(ApiTestCase):
    def test_peer_chat_inbox_and_messages(self):
        PeerChat.objects.create(student=self.learner, instructor=self.tutor, message='hello tutor',
                                content_type=ContentType.objects.get_for_model(STUDENT), object_id=self.learner.id)
        self.auth(self.tutor)
        inbox = self.client.get(self.url('peer-chat-list')).data
        self.assertEqual(len(inbox), 1)
        self.assertEqual(inbox[0]['partner']['USER_NAME'], 'learner1')
        self.assertEqual(inbox[0]['last']['message'], 'hello tutor')

        room = self.url('peer-chat-room', 'tutor1', 'learner1')
        r = self.client.post(room, {'message': 'hello learner'}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data['sender_cat'], 'instructor')
        self.assertEqual([m['message'] for m in self.client.get(room).data], ['hello tutor', 'hello learner'])

        # the room opens with the most recent 20 messages, oldest first
        for i in range(30):
            PeerChat.objects.create(student=self.learner, instructor=self.tutor, message=f'msg {i}',
                                    content_type=ContentType.objects.get_for_model(STUDENT), object_id=self.learner.id)
        history = self.client.get(room).data
        self.assertEqual(len(history), 20)
        self.assertEqual(history[-1]['message'], 'msg 29')
        self.assertEqual(history[0]['message'], 'msg 10')
        self.assertEqual(len(self.client.get(room + '?limit=5').data), 5)

        # a third party cannot read the room
        self.auth(self.stranger)
        self.assertEqual(self.client.get(room).status_code, 403)
