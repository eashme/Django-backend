from django.db import models
from db.base_model import BaseModel, BaseManager
from django.utils.timezone import now

# Create your models here.

class Machine(models.Model):
    """用户使用机器表
    机器和用户进行绑定
    使用人
    mac地址
    is_active是否激活
    """
    user = models.ForeignKey(to='users.User', verbose_name='用户')
    mac_add = models.CharField(max_length=48, verbose_name='Mac地址')
    is_active = models.BooleanField(default=False, verbose_name='是否已启用')
    last_ip_add = models.CharField(max_length=20, verbose_name='Mac地址')
    last_login = models.DateTimeField(default=now, verbose_name='最近一次登录时间')
    create_time = models.DateField(auto_now_add=True, verbose_name='创建时间')
    is_delete = models.BooleanField(default=False, verbose_name='删除标记')

    objects = BaseManager()

    class Meta:
        db_table = 'machine_info'


class Program(BaseModel):
    """ 程序表
    title       程序标题(代码编号)
    fornum      所属论坛
    version     版本号
    is_active   是否激活可用
    description 程序描述
    """
    title = models.CharField(max_length=24, verbose_name='标题')
    fornum = models.ForeignKey(to='scripts.Fornum', verbose_name='所属论坛')
    version = models.CharField(max_length=32, verbose_name='版本号')
    is_active = models.BooleanField(default=True, verbose_name='是否激活可用')
    description = models.TextField(verbose_name='程序描述', null=True, default='')

    class Meta:
        db_table = 'program'
