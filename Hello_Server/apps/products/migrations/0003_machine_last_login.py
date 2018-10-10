# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_machine_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='machine',
            name='last_login',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='创建时间'),
        ),
    ]
