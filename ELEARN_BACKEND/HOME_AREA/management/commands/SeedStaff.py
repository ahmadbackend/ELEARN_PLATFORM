"""
Create the back-office accounts: one admin and the moderators.

    python manage.py SeedStaff

Idempotent. Existing accounts keep their password and only have their role
corrected; new ones are created with an unusable password, because this
command does not deal in credentials at all -- `DumpUsers` sets and records
them. That keeps password generation in exactly one place.

    python manage.py SeedStaff --moderators 3
    python manage.py SeedStaff --promote alice      # make an existing user a moderator
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from HOME_AREA.staff import MODERATOR_GROUP, sync_moderator_group

User = get_user_model()

ADMIN = {'username': 'admin', 'email': 'admin@elearn.local',
         'first_name': 'Site', 'last_name': 'Administrator'}

# real names and addresses so the admin's user list reads like people, not placeholders
MODERATORS = [
    {'username': 'moderator1', 'email': 'nadia.karim@elearn.local',
     'first_name': 'Nadia', 'last_name': 'Karim'},
    {'username': 'moderator2', 'email': 'tomas.lindqvist@elearn.local',
     'first_name': 'Tomas', 'last_name': 'Lindqvist'},
    {'username': 'moderator3', 'email': 'grace.osei@elearn.local',
     'first_name': 'Grace', 'last_name': 'Osei'},
]


class Command(BaseCommand):
    help = 'Create the admin and moderator accounts and the Moderators permission group.'

    def add_arguments(self, parser):
        parser.add_argument('--moderators', type=int, default=2,
                            help=f'how many moderator accounts to create (max {len(MODERATORS)})')
        parser.add_argument('--promote', action='append', default=[], metavar='USERNAME',
                            help='also make this existing user a moderator; repeatable')

    @transaction.atomic
    def handle(self, *args, **options):
        wanted = options['moderators']
        if not 0 <= wanted <= len(MODERATORS):
            raise CommandError(f'--moderators must be between 0 and {len(MODERATORS)}')

        group, created, permissions, missing = sync_moderator_group()
        self.stdout.write(
            f'{"created" if created else "updated"} group "{MODERATOR_GROUP}" '
            f'with {len(permissions)} permissions')
        if missing:
            self.stderr.write(self.style.WARNING(
                'these permissions do not exist (run migrate first?): ' + ', '.join(map(str, missing))))

        self.ensure(ADMIN, superuser=True, group=None)
        for profile in MODERATORS[:wanted]:
            self.ensure(profile, superuser=False, group=group)

        for username in options['promote']:
            user = User.objects.filter(username=username).first()
            if user is None:
                raise CommandError(f'no user named "{username}"')
            user.is_staff = True
            user.save(update_fields=['is_staff'])
            user.groups.add(group)
            self.stdout.write(self.style.SUCCESS(f'promoted {username} to moderator'))

        self.stdout.write(self.style.SUCCESS(
            '\nRun `python manage.py DumpUsers --out users.txt` to set and record their passwords.'))

    def ensure(self, profile, superuser, group):
        """Create the account if missing, and make its role match either way."""
        user, created = User.objects.get_or_create(
            username=profile['username'],
            defaults={k: v for k, v in profile.items() if k != 'username'},
        )
        if created:
            # DumpUsers is what hands out passwords; until then the account cannot log in
            user.set_unusable_password()
        user.is_staff = True
        user.is_superuser = superuser
        user.is_active = True
        for field in ('email', 'first_name', 'last_name'):
            setattr(user, field, profile[field])
        user.save()

        # a superuser has every permission implicitly, so the group would be noise
        if group is not None:
            user.groups.add(group)
        else:
            user.groups.clear()

        role = 'admin (superuser)' if superuser else 'moderator'
        verb = 'created' if created else 'updated'
        style = self.style.SUCCESS if created else self.style.NOTICE
        self.stdout.write(style(f'{verb} {role}: {user.username} <{user.email}>'))
