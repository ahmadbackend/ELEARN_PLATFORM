# Generated by Django 5.0 on 2024-08-24 08:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HOME_AREA', '0008_remove_courses_rating_alter_reviews_user_name_rating'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rating',
            name='RATING',
            field=models.IntegerField(blank=True, choices=[(2, '2'), (4, '4'), (1, '1'), (5, '5'), (3, '3')], null=True),
        ),
    ]
