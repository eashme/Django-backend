# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.auth.models
import django.core.validators
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('scripts', '0001_initial'),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('password', models.CharField(verbose_name='password', max_length=128)),
                ('last_login', models.DateTimeField(verbose_name='last login', null=True, blank=True)),
                ('is_superuser', models.BooleanField(default=False, verbose_name='superuser status', help_text='Designates that this user has all permissions without explicitly assigning them.')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.', 'invalid')], unique=True, verbose_name='username', max_length=30, help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.')),
                ('first_name', models.CharField(verbose_name='first name', max_length=30, blank=True)),
                ('last_name', models.CharField(verbose_name='last name', max_length=30, blank=True)),
                ('email', models.EmailField(verbose_name='email address', max_length=254, blank=True)),
                ('is_staff', models.BooleanField(default=False, verbose_name='staff status', help_text='Designates whether the user can log into this admin site.')),
                ('is_active', models.BooleanField(default=True, verbose_name='active', help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('create_time', models.DateField(verbose_name='创建时间', auto_now_add=True)),
                ('founder', models.IntegerField(default=-1, verbose_name='创建人', null=True)),
                ('update_time', models.DateField(verbose_name='更新时间', auto_now=True)),
                ('update_person', models.IntegerField(default=-1, verbose_name='更新人', null=True)),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('role', models.SmallIntegerField(default=1, verbose_name='用户角色', choices=[(1, '管理员'), (2, '后台操作员'), (3, '代理商'), (4, '广告主'), (5, '广告操作员'), (6, '临时帐号')])),
                ('groups', models.ManyToManyField(to='auth.Group', related_query_name='user', blank=True, related_name='user_set', verbose_name='groups', help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.')),
                ('user_permissions', models.ManyToManyField(to='auth.Permission', related_query_name='user', blank=True, related_name='user_set', verbose_name='user permissions', help_text='Specific permissions for this user.')),
            ],
            options={
                'verbose_name_plural': '用户表',
                'verbose_name': '用户表',
                'db_table': 'user',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='MemberShip',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('create_time', models.DateField(verbose_name='创建时间', auto_now_add=True)),
                ('founder', models.IntegerField(default=-1, verbose_name='创建人', null=True)),
                ('update_time', models.DateField(verbose_name='更新时间', auto_now=True)),
                ('update_person', models.IntegerField(default=-1, verbose_name='更新人', null=True)),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('end_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='最后可用时间')),
                ('master', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='m', verbose_name='主用户')),
                ('slave', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='s', verbose_name='从用户')),
            ],
            options={
                'verbose_name_plural': '用户关系表',
                'verbose_name': '用户关系表',
                'db_table': 'user_relationship',
            },
        ),
        migrations.CreateModel(
            name='UserFornumRelation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('create_time', models.DateField(verbose_name='创建时间', auto_now_add=True)),
                ('founder', models.IntegerField(default=-1, verbose_name='创建人', null=True)),
                ('update_time', models.DateField(verbose_name='更新时间', auto_now=True)),
                ('update_person', models.IntegerField(default=-1, verbose_name='更新人', null=True)),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('fornum', models.ForeignKey(to='scripts.Fornum', verbose_name='论坛')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name_plural': '用户论坛对应表',
                'verbose_name': '用户论坛对应表',
                'db_table': 'user_fornum_rel',
            },
        ),
        migrations.CreateModel(
            name='UserInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('create_time', models.DateField(verbose_name='创建时间', auto_now_add=True)),
                ('founder', models.IntegerField(default=-1, verbose_name='创建人', null=True)),
                ('update_time', models.DateField(verbose_name='更新时间', auto_now=True)),
                ('update_person', models.IntegerField(default=-1, verbose_name='更新人', null=True)),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('remarks', models.TextField(verbose_name='备注', null=True, max_length=500)),
                ('telephone', models.CharField(default='-1', verbose_name='联系电话', null=True, max_length=24)),
                ('gender', models.SmallIntegerField(default=1, verbose_name='性别', null=True, choices=[(0, '男'), (1, '女')])),
                ('accounts', models.SmallIntegerField(default=1, verbose_name='可开户数')),
                ('has_accounts', models.SmallIntegerField(default=0, verbose_name='已开户数')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name_plural': '用户信息表',
                'verbose_name': '用户信息表',
                'db_table': 'user_info',
            },
        ),
    ]
