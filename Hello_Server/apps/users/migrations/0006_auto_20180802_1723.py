# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import apps.users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_auto_20180802_1614'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', apps.users.models.MyUserManager()),
            ],
        ),
    ]
