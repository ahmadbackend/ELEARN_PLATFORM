"""
Write every account and its password to a plain text file.

    python manage.py DumpUsers --out users.txt

Passwords are stored as hashes, so an existing password can only be *reported*
when we already know a candidate for it and it verifies -- which is the case
for the learners and tutors loaded from INSTRUCTOR/CSVs. For every other
account there is nothing to recover, so this command generates a new password,
sets it and records that. Use --no-reset to leave those alone and list them as
unknown instead.

The output is plaintext credentials: it is gitignored, it must never be written
under MEDIA_ROOT (nginx serves that directory), and it is a development and
demo convenience, not something to keep next to a real deployment.
"""
import csv
import io
import os
import secrets
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from HOME_AREA.passwords import check_user_password, hash_password
from HOME_AREA.staff import MODERATOR_GROUP
from INSTRUCTOR.models import INSTRUCTOR
from STUDENT.models import STUDENT

User = get_user_model()

CSV_DIR = os.path.join(settings.BASE_DIR, 'INSTRUCTOR', 'CSVs')
# the platform password rule: 8-12 chars, letters and digits, >=1 lowercase and >=1 digit
PLATFORM_ALPHABET = string.ascii_letters + string.digits
STAFF_ALPHABET = string.ascii_letters + string.digits + '!@#$%^&*-_=+'


def platform_password(length=12):
    while True:
        candidate = ''.join(secrets.choice(PLATFORM_ALPHABET) for _ in range(length))
        if any(c.islower() for c in candidate) and any(c.isdigit() for c in candidate):
            return candidate


def staff_password(length=16):
    return ''.join(secrets.choice(STAFF_ALPHABET) for _ in range(length))


def seeded_passwords():
    """EMAIL -> password, from the CSVs the LoadData command seeds from."""
    known = {}
    for name in ('student.csv', 'instructor.csv'):
        path = os.path.join(CSV_DIR, name)
        if not os.path.exists(path):
            continue
        with io.open(path, encoding='utf-8-sig') as fh:
            for row in csv.DictReader(fh):
                if row.get('EMAIL') and row.get('PASSWORD'):
                    known[row['EMAIL'].strip()] = row['PASSWORD'].strip()
    return known


class Command(BaseCommand):
    help = 'Write all accounts and their passwords to a plain text file.'

    def add_arguments(self, parser):
        parser.add_argument('--out', default='users.txt', help='output file (default: users.txt)')
        parser.add_argument('--no-reset', action='store_true',
                            help='do not generate a password for accounts whose password is unknown')

    def handle(self, *args, **options):
        reset = not options['no_reset']
        known = seeded_passwords()
        self.reset_count = 0

        sections = [
            ('ADMINS', self.staff_rows(superuser=True, reset=reset)),
            ('MODERATORS', self.staff_rows(superuser=False, reset=reset)),
            ('TUTORS (instructors)', self.platform_rows(INSTRUCTOR, known, reset)),
            ('LEARNERS (students)', self.platform_rows(STUDENT, known, reset)),
        ]

        path = os.path.abspath(options['out'])
        with io.open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(self.render(sections))

        total = sum(len(rows) for _, rows in sections)
        self.stdout.write(self.style.SUCCESS(f'wrote {total} accounts to {path}'))
        if self.reset_count:
            self.stdout.write(self.style.WARNING(
                f'{self.reset_count} password(s) could not be recovered and were reset to a new one. '
                'Any API token issued to those accounts is now invalid.'))
        self.stdout.write(self.style.WARNING('This file contains plaintext passwords. Do not commit it.'))

    # ------------------------------------------------------------------ rows
    def staff_rows(self, superuser, reset):
        query = User.objects.filter(is_staff=True, is_superuser=superuser).order_by('username')
        if not superuser:
            query = query.filter(groups__name=MODERATOR_GROUP)
        rows = []
        for user in query.distinct():
            # nothing to verify a django user's password against, so it is always regenerated
            if reset:
                password = staff_password()
                user.set_password(password)
                user.save(update_fields=['password'])
                self.reset_count += 1
            else:
                password = '(unknown - hashed)'
            rows.append({
                'username': user.username,
                'email': user.email,
                'name': (user.get_full_name() or '').strip(),
                'password': password,
                'note': 'superuser' if superuser else MODERATOR_GROUP.lower().rstrip('s'),
            })
        return rows

    def platform_rows(self, model, known, reset):
        rows = []
        for user in model.objects.all().order_by('USER_NAME'):
            candidate = known.get(user.EMAIL)
            if candidate and check_user_password(user, candidate):
                password, note = candidate, 'seeded'
            elif reset:
                password = platform_password()
                user.PASSWORD = hash_password(password)
                user.save(update_fields=['PASSWORD'])
                self.reset_count += 1
                note = 'reset'
            else:
                password, note = '(unknown - hashed)', 'unknown'
            if not user.Isactive:
                note += ', not activated'
            rows.append({
                'username': user.USER_NAME,
                'email': user.EMAIL,
                'name': f'{user.FIRST_NAME} {user.LAST_NAME}'.strip(),
                'password': password,
                'note': note,
            })
        return rows

    # ------------------------------------------------------------------ output
    def render(self, sections):
        out = [
            'ELEARN accounts',
            '=' * 72,
            '',
            'Generated by `manage.py DumpUsers`. PLAINTEXT PASSWORDS - do not commit,',
            'do not deploy, regenerate for anything that is not a local demo.',
            '',
            'Where each kind of account signs in:',
            '  admins, moderators   /admin/          (Django admin)',
            '  tutors, learners     the SPA          (pick "Tutor" or "Learner" on the login form)',
            '',
            'Passwords marked "seeded" are the original ones from INSTRUCTOR/CSVs.',
            'Passwords marked "reset" could not be recovered from the stored hash, so a',
            'new one was generated and saved.',
            '',
        ]
        for title, rows in sections:
            out.append(title)
            out.append('-' * 72)
            if not rows:
                out.extend(['(none)', ''])
                continue
            widths = {key: max(len(key), max(len(str(r[key])) for r in rows))
                      for key in ('username', 'email', 'name', 'password', 'note')}
            header = '  '.join(key.upper().ljust(widths[key])
                               for key in ('username', 'email', 'name', 'password', 'note'))
            out.append(header)
            out.append('  '.join('-' * widths[key]
                                 for key in ('username', 'email', 'name', 'password', 'note')))
            for r in rows:
                out.append('  '.join(str(r[key]).ljust(widths[key])
                                     for key in ('username', 'email', 'name', 'password', 'note')))
            out.append('')
        return '\n'.join(out) + '\n'
