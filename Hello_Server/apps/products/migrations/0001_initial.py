# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scripts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Machine',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('mac_add', models.CharField(verbose_name='Mac地址', max_length=48)),
                ('is_active', models.BooleanField(default=False, verbose_name='是否已启用')),
                ('last_ip_add', models.CharField(verbose_name='Mac地址', max_length=20)),
                ('create_time', models.DateField(verbose_name='创建时间', auto_now_add=True)),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
            ],
            options={
                'db_table': 'machine_info',
            },
        ),
        migrations.CreateModel(
            name='Program',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('create_time', models.DateField(verbose_name='创建时间', auto_now_add=True)),
                ('founder', models.IntegerField(default=-1, verbose_name='创建人', null=True)),
                ('update_time', models.DateField(verbose_name='更新时间', auto_now=True)),
                ('update_person', models.IntegerField(default=-1, verbose_name='更新人', null=True)),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('title', models.CharField(verbose_name='标题', max_length=24)),
                ('version', models.CharField(verbose_name='版本号', max_length=32)),
                ('is_active', models.BooleanField(default=True, verbose_name='是否激活可用')),
                ('description', models.TextField(default='', verbose_name='程序描述', null=True)),
                ('fornum', models.ForeignKey(to='scripts.Fornum', verbose_name='所属论坛')),
            ],
            options={
                'db_table': 'program',
            },
        ),
    ]
