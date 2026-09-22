"""
Tests for the back-office roles: what an admin can reach, what a moderator can
reach, and what neither a moderator nor a platform user can touch.

Run with:  python manage.py test HOME_AREA.tests_staff
"""
import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from HOME_AREA.models import COURSES
from HOME_AREA.passwords import hash_password
from HOME_AREA.staff import MODERATOR_GROUP, sync_moderator_group
from INSTRUCTOR.models import INSTRUCTOR
from STUDENT.models import STUDENT

User = get_user_model()

# force_login() defaults to AUTHENTICATION_BACKENDS[0], which is the learner backend.
# Back-office accounts are django.contrib.auth users, so they authenticate through
# ModelBackend and the session has to say so.
MODEL_BACKEND = 'django.contrib.auth.backends.ModelBackend'

TEST_SETTINGS = dict(
    MEDIA_ROOT=tempfile.mkdtemp(),
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
)


def png(name='pic.png'):
    from PIL import Image
    buf = BytesIO()
    Image.new('RGB', (1, 1)).save(buf, 'PNG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')


@override_settings(**TEST_SETTINGS)
class StaffTestCase(TestCase):
    def setUp(self):
        group, *_ = sync_moderator_group()
        self.admin = User.objects.create_superuser('admin', 'admin@elearn.local', 'adminpass123')
        self.moderator = User.objects.create_user('mod', 'mod@elearn.local', 'modpass123',
                                                  is_staff=True)
        self.moderator.groups.add(group)

        self.tutor = INSTRUCTOR.objects.create(
            FIRST_NAME='Tina', LAST_NAME='Tutor', USER_NAME='tutor1', EMAIL='tutor1@example.com',
            PHONE='1000001', PASSWORD=hash_password('password1'), PICTURE=png(), Isactive=True)
        self.learner = STUDENT.objects.create(
            FIRST_NAME='Lee', LAST_NAME='Learner', USER_NAME='learner1',
            EMAIL='learner1@example.com', PHONE='2000001',
            PASSWORD=hash_password('password1'), Isactive=True)
        self.course = COURSES.objects.create(COURSE_NAME='Django 101', COVER_PHOTO=png(),
                                             instructor=self.tutor)


class ModeratorPermissionTests(StaffTestCase):
    def test_moderator_can_moderate_content(self):
        self.client.force_login(self.moderator, backend=MODEL_BACKEND)
        for url in ('/admin/HOME_AREA/courses/', '/admin/HOME_AREA/reviews/',
                    '/admin/HOME_AREA/peerchat/', '/admin/INSTRUCTOR/block_list/',
                    f'/admin/STUDENT/student/{self.learner.id}/change/'):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_moderator_cannot_touch_accounts_or_permissions(self):
        self.client.force_login(self.moderator, backend=MODEL_BACKEND)
        for url in ('/admin/auth/user/', '/admin/auth/group/',
                    '/admin/STUDENT/student/add/', '/admin/INSTRUCTOR/instructor/add/',
                    '/admin/STUDENT/code_generator/'):
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_moderator_cannot_set_a_learners_password(self):
        """Suspending an account is moderation; changing its password is impersonation."""
        self.client.force_login(self.moderator, backend=MODEL_BACKEND)
        form = self.client.get(f'/admin/STUDENT/student/{self.learner.id}/change/').content.decode()
        self.assertNotIn('name="PASSWORD"', form)

        # and the field is ignored even if it is posted by hand
        before = STUDENT.objects.get(pk=self.learner.pk).PASSWORD
        self.client.post(f'/admin/STUDENT/student/{self.learner.id}/change/', {
            'FIRST_NAME': 'Lee', 'LAST_NAME': 'Learner', 'USER_NAME': 'learner1',
            'EMAIL': 'learner1@example.com', 'PHONE': '2000001',
            'PASSWORD': 'hijacked99', 'Isactive': 'on', 'is_active': 'on',
        })
        self.assertEqual(STUDENT.objects.get(pk=self.learner.pk).PASSWORD, before)

    def test_admin_can_set_a_password_and_it_is_stored_hashed(self):
        self.client.force_login(self.admin, backend=MODEL_BACKEND)
        form = self.client.get(f'/admin/STUDENT/student/{self.learner.id}/change/').content.decode()
        self.assertIn('name="PASSWORD"', form)

        self.client.post(f'/admin/STUDENT/student/{self.learner.id}/change/', {
            'FIRST_NAME': 'Lee', 'LAST_NAME': 'Learner', 'USER_NAME': 'learner1',
            'EMAIL': 'learner1@example.com', 'PHONE': '2000001',
            'PASSWORD': 'brandnew99', 'Isactive': 'on', 'is_active': 'on',
        })
        from HOME_AREA.passwords import check_user_password, is_hashed
        learner = STUDENT.objects.get(pk=self.learner.pk)
        self.assertTrue(is_hashed(learner.PASSWORD))
        self.assertNotEqual(learner.PASSWORD, 'brandnew99')
        self.assertTrue(check_user_password(learner, 'brandnew99'))

    def test_admin_reaches_everything_the_moderator_cannot(self):
        self.client.force_login(self.admin, backend=MODEL_BACKEND)
        for url in ('/admin/auth/user/', '/admin/auth/group/', '/admin/STUDENT/student/add/'):
            self.assertEqual(self.client.get(url).status_code, 200, url)


class AdminAccessTests(StaffTestCase):
    def test_a_learner_cannot_log_into_the_admin(self):
        """A platform account is not a back-office account, even if the address collides."""
        response = self.client.post('/admin/login/', {
            'username': 'learner1@example.com', 'password': 'password1'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Site administration')
        self.assertFalse(response.context['user'].is_authenticated)

    def test_a_tutor_cannot_log_into_the_admin(self):
        response = self.client.post('/admin/login/', {
            'username': 'tutor1@example.com', 'password': 'password1'}, follow=True)
        self.assertNotContains(response, 'Site administration')
        self.assertFalse(response.context['user'].is_authenticated)

    def test_platform_users_are_never_staff(self):
        self.assertFalse(self.learner.is_staff)
        self.assertFalse(self.learner.is_superuser)
        self.assertFalse(self.tutor.is_staff)
        self.assertFalse(self.tutor.is_superuser)


class GroupSyncTests(StaffTestCase):
    def test_sync_is_idempotent_and_resolves_every_permission(self):
        group, created, permissions, missing = sync_moderator_group()
        self.assertFalse(created)                 # setUp made it already
        self.assertEqual(missing, [], 'MODERATOR_PERMISSIONS names a permission that does not exist')
        self.assertEqual(group.name, MODERATOR_GROUP)
        self.assertEqual(group.permissions.count(), len(permissions))

        # running it again does not accumulate duplicates
        sync_moderator_group()
        self.assertEqual(group.permissions.count(), len(permissions))
