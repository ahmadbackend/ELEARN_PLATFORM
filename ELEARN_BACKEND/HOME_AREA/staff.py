"""
Back-office roles.

Admins and moderators are ordinary django.contrib.auth users and log in at
/admin/ like any Django project. They are a different population from the
STUDENT and INSTRUCTOR tables, which hold the platform's learners and tutors
and never get access to the admin site.

  admin      superuser: everything
  moderator  is_staff + the "Moderators" group below

A moderator moderates *content and conduct*: they can take down a course, a
lecture, a review, a comment or a chat message, see who is enrolled, and block
a learner on a tutor's behalf. They deliberately cannot create or delete
accounts, edit anybody's password, or hand out permissions -- that is what
separates a moderator from an admin.
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

MODERATOR_GROUP = 'Moderators'

# "app_label.ModelName": the actions a moderator gets on it
MODERATOR_PERMISSIONS = {
    # take down content
    'HOME_AREA.COURSES': ['view', 'change', 'delete'],
    'HOME_AREA.LECTURES': ['view', 'change', 'delete'],
    'HOME_AREA.REVIEWS': ['view', 'delete'],
    'HOME_AREA.Rating': ['view', 'delete'],
    'HOME_AREA.COMMENTS': ['view', 'delete'],
    'HOME_AREA.PeerChat': ['view', 'delete'],
    # look at people and enrolments, and act on conduct
    'STUDENT.STUDENT': ['view', 'change'],
    'STUDENT.COURSE_LIST': ['view', 'delete'],
    'INSTRUCTOR.INSTRUCTOR': ['view', 'change'],
    'INSTRUCTOR.BLOCK_LIST': ['view', 'add', 'delete'],
}


def moderator_permissions():
    """The Permission rows MODERATOR_PERMISSIONS names, skipping anything missing."""
    found, missing = [], []
    for label, actions in MODERATOR_PERMISSIONS.items():
        app_label, model = label.split('.')
        try:
            content_type = ContentType.objects.get(app_label=app_label, model=model.lower())
        except ContentType.DoesNotExist:
            missing.extend(f'{label}.{action}' for action in actions)
            continue
        for action in actions:
            codename = f'{action}_{model.lower()}'
            permission = Permission.objects.filter(content_type=content_type, codename=codename).first()
            (found if permission else missing).append(permission or f'{label}.{action}')
    return found, missing


def sync_moderator_group():
    """Create the Moderators group and set its permissions to exactly the list above.

    Idempotent: run it again after changing MODERATOR_PERMISSIONS and the group
    catches up, including permissions that were removed from the list.
    """
    group, created = Group.objects.get_or_create(name=MODERATOR_GROUP)
    permissions, missing = moderator_permissions()
    group.permissions.set(permissions)
    return group, created, permissions, missing
