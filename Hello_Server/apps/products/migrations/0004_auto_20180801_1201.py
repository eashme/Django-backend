# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_machine_last_login'),
    ]

    operations = [
        migrations.AlterField(
            model_name='machine',
            name='last_login',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='最近一次登录时间'),
        ),
    ]
