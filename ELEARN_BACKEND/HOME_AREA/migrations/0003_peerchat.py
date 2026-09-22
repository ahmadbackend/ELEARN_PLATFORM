import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HOME_AREA', '0002_initial'),
        ('INSTRUCTOR', '0001_initial'),
        ('STUDENT', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='PeerChat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(max_length=1000)),
                ('object_id', models.PositiveIntegerField()),
                ('TimeStamp', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('instructor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='peer_chats', to='INSTRUCTOR.instructor')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='peer_chats', to='STUDENT.student')),
            ],
            options={
                'ordering': ['TimeStamp'],
            },
        ),
    ]
