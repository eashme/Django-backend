# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Fornum',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('create_time', models.DateField(verbose_name='创建时间', auto_now_add=True)),
                ('founder', models.IntegerField(default=-1, verbose_name='创建人', null=True)),
                ('update_time', models.DateField(verbose_name='更新时间', auto_now=True)),
                ('update_person', models.IntegerField(default=-1, verbose_name='更新人', null=True)),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('title', models.CharField(default='null', verbose_name='论坛代号', max_length=24)),
                ('fornum_name', models.CharField(default='null', verbose_name='论坛名称', max_length=24)),
                ('description', models.TextField(default='', verbose_name='论坛描述', null=True)),
            ],
            options={
                'verbose_name_plural': '论坛信息表',
                'verbose_name': '论坛信息表',
                'db_table': 'forum_info',
            },
        ),
        migrations.CreateModel(
            name='JavaScriptCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('create_time', models.DateField(verbose_name='创建时间', auto_now_add=True)),
                ('founder', models.IntegerField(default=-1, verbose_name='创建人', null=True)),
                ('update_time', models.DateField(verbose_name='更新时间', auto_now=True)),
                ('update_person', models.IntegerField(default=-1, verbose_name='更新人', null=True)),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('title', models.CharField(default='null', verbose_name='论坛名称', max_length=24)),
                ('js_code', models.TextField(default='', verbose_name='JS代码')),
                ('description', models.TextField(verbose_name='Js代码描述', max_length=500)),
                ('fornum', models.ForeignKey(to='scripts.Fornum', verbose_name='所属论坛')),
            ],
            options={
                'verbose_name_plural': 'js脚本表',
                'verbose_name': 'js脚本表',
                'db_table': 'java_script_table',
            },
        ),
    ]
