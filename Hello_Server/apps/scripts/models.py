from django.db import models
from db.base_model import BaseModel


# Create your models here.

class JavaScriptCode(BaseModel):
    title = models.CharField(max_length=24, verbose_name='论坛名称', default='null')
    fornum = models.ForeignKey('Fornum', verbose_name='所属论坛')
    js_code = models.TextField(verbose_name='JS代码', default='')
    description = models.TextField(max_length=500, verbose_name='Js代码描述')

    class Meta:
        db_table = 'java_script_table'
        verbose_name = 'js脚本表'
        verbose_name_plural = verbose_name


class Fornum(BaseModel):
    APP_TYPE = {
        0: 'windows应用',
        1: '手机app'
    }
    APP_CHOICES = (
        (0,'windows应用'),
        (1, '手机app'),
    )

    title = models.CharField(max_length=24, verbose_name='论坛代号', default='null')
    fornum_name = models.CharField(max_length=24, verbose_name='论坛名称', default='null')
    description = models.TextField(verbose_name='论坛描述', null=True, default='')
    app_type = models.SmallIntegerField(choices=APP_CHOICES, default=0, verbose_name='app类型')

    class Meta:
        db_table = 'forum_info'
        verbose_name = '论坛信息表'
        verbose_name_plural = verbose_name
