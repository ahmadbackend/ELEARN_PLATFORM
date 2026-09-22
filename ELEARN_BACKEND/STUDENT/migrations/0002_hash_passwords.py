"""
Move STUDENT.PASSWORD from plaintext to a Django password hash.

The column is widened first, then every existing row is hashed in place.
Nobody's password changes: the same plaintext still logs in, it is simply
verified against the hash from now on. Irreversible by design -- a hash
cannot be turned back into the password it came from.
"""
from django.db import migrations, models
import django.core.validators

from HOME_AREA.passwords import PASSWORD_HASH_MAX_LENGTH, hash_password, is_hashed


def hash_existing(apps, schema_editor):
    Model = apps.get_model('STUDENT', 'STUDENT')
    rows = []
    for row in Model.objects.all().only('id', 'PASSWORD').iterator():
        if not is_hashed(row.PASSWORD):
            row.PASSWORD = hash_password(row.PASSWORD)
            rows.append(row)
    if rows:
        Model.objects.bulk_update(rows, ['PASSWORD'], batch_size=200)


class Migration(migrations.Migration):

    dependencies = [
        ('STUDENT', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='PASSWORD',
            field=models.CharField(
                max_length=PASSWORD_HASH_MAX_LENGTH,
                validators=[
                    django.core.validators.MinLengthValidator(8),
                    django.core.validators.RegexValidator(
                        message='Password must be 8 to 12 letters and digits, '
                                'with at least one lowercase letter and one digit.',
                        regex='^(?=.*[a-z])(?=.*\d)[a-zA-Z\d]{8,12}$',
                    ),
                ],
            ),
        ),
        migrations.RunPython(hash_existing, migrations.RunPython.noop),
    ]
