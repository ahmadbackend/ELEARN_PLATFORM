# Generated by Django 5.0 on 2024-08-23 16:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HOME_AREA', '0006_alter_reviews_user_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='reviews',
            options={'ordering': ['-WRITING_DATE']},
        ),
        migrations.AddField(
            model_name='comments',
            name='WRITING_DATE',
            field=models.DateTimeField(auto_created=True, auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='reviews',
            name='WRITING_DATE',
            field=models.DateTimeField(auto_created=True, auto_now_add=True, null=True),
        ),
    ]
