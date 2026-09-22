"""
Drop the per-course chat room.

It only ever backed the removed Django template pages: its websocket consumer
took the sender's name from the browser, so any connected client could post as
anyone. The SPA uses the private learner <-> tutor PeerChat room instead.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('HOME_AREA', '0003_peerchat'),
    ]

    operations = [
        migrations.DeleteModel(name='ChatRoom'),
    ]
