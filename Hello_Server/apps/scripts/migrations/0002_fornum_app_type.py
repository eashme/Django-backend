# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scripts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='fornum',
            name='app_type',
            field=models.SmallIntegerField(choices=[(0, 'windows应用'), (1, '手机app')], default=0, verbose_name='app类型'),
        ),
    ]
