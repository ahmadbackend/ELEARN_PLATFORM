# Generated by Django 5.0 on 2024-08-30 15:50

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('HOME_AREA', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='COURSE_LIST',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='HOME_AREA.courses')),
            ],
        ),
        migrations.CreateModel(
            name='STUDENT',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('FIRST_NAME', models.CharField(max_length=50)),
                ('LAST_NAME', models.CharField(max_length=50)),
                ('USER_NAME', models.CharField(max_length=50, unique=True)),
                ('EMAIL', models.EmailField(max_length=254, unique=True)),
                ('PHONE', models.CharField(max_length=15, unique=True)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('PICTURE', models.ImageField(blank=True, null=True, upload_to='images/')),
                ('PASSWORD', models.CharField(max_length=12, validators=[django.core.validators.MinLengthValidator(8), django.core.validators.RegexValidator(message='Password must contain at least one lowercase letter and one digit.', regex='^(?=.*[a-z])(?=.*\\d)[a-zA-Z\\d]{8,}$')])),
                ('Isactive', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('courseList', models.ManyToManyField(through='STUDENT.COURSE_LIST', to='HOME_AREA.courses')),
            ],
            options={
                'verbose_name_plural': 'Students',
                'permissions': [('ENROLL', 'LEAVE_REVIEW')],
            },
        ),
        migrations.AddField(
            model_name='course_list',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='STUDENT.student'),
        ),
        migrations.CreateModel(
            name='CODE_GENERATOR',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ACTIVATION_CODE', models.CharField(max_length=6)),
                ('EMAIL', models.EmailField(blank=True, max_length=254, null=True)),
                ('USER_VERIFIER', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='STUDENT.student')),
            ],
        ),
    ]
