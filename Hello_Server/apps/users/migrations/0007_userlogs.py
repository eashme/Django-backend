# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_auto_20180802_1723'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserLogs',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('load_ip', models.CharField(max_length=50, verbose_name='用户IP登陆的地址')),
                ('mac_add', models.CharField(max_length=50, blank=True, verbose_name='用户登陆的mac地址', default='')),
                ('softwareType', models.IntegerField(verbose_name='软件所属论坛id')),
                ('create_time', models.DateTimeField(auto_now=True, verbose_name='记录创建时间')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='用户外键')),
            ],
            options={
                'db_table': 'user_logs',
                'verbose_name_plural': '用户登陆信息表',
                'verbose_name': '用户登陆信息表',
            },
        ),
    ]
