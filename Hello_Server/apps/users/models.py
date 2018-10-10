from django.db import models
from db.base_model import BaseModel
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils.timezone import now


# Create your models here.

class MyUserManager(UserManager):
    def get_query_set(self):
        return models.query.QuerySet(self.model, using=self._db)

    def delete(self):
        self.get_query_set().delete()

    def all(self):
        return self.get_query_set().filter(is_delete=False)

    def filter(self, *args, **kwargs):
        return self.get_query_set().filter(*args, **kwargs).filter(is_delete=False)


class User(BaseModel, AbstractUser):
    """用户模型类"""

    Role = {
        1: '管理员',
        2: '后台操作员',
        3: '代理商',
        4: '广告主',
        5: '广告操作员',
        6: '临时帐号'
    }

    Role_CHOICES = (
        (1, '管理员'),
        (2, '后台操作员'),
        (3, '代理商'),
        (4, '广告主'),
        (5, '广告操作员'),
        (6, '临时帐号')
    )
    role = models.SmallIntegerField(choices=Role_CHOICES, default=1, verbose_name='用户角色')
    name = models.CharField(max_length=24, verbose_name='姓名', default='')

    objects = MyUserManager()

    class Meta:
        db_table = 'user'
        verbose_name = '用户表'
        verbose_name_plural = verbose_name


class UserInfo(BaseModel):
    """用户信息模型类"""

    Gender = {
        0: '男',
        1: '女'
    }
    Gender_CHOICES = (
        (0, '男'),
        (1, '女'),
    )

    user = models.ForeignKey('User', verbose_name='用户')
    remarks = models.TextField(max_length=500, verbose_name='备注', null=True)
    telephone = models.CharField(max_length=24, null=True, verbose_name='联系电话', default='-1')
    gender = models.SmallIntegerField(choices=Gender_CHOICES, default=1, verbose_name='性别', null=True)
    accounts = models.SmallIntegerField(default=1, verbose_name='可开户数')
    has_accounts = models.SmallIntegerField(default=0, verbose_name='已开户数')

    class Meta:
        db_table = 'user_info'
        verbose_name = '用户信息表'
        verbose_name_plural = verbose_name


class MemberShip(BaseModel):
    """
    主从关系
    """

    master = models.ForeignKey(to='User', related_name='m', verbose_name='主用户')
    slave = models.ForeignKey(to='User', related_name='s', verbose_name='从用户')
    # 默认为创建之后5小时
    end_time = models.DateTimeField(default=now, verbose_name='最后可用时间')

    class Meta:
        db_table = 'user_relationship'
        verbose_name = '用户关系表'
        verbose_name_plural = verbose_name


class UserFornumRelation(BaseModel):
    """
    用户和程序的关联关系表
    """
    user = models.ForeignKey('User', verbose_name='用户')
    fornum = models.ForeignKey('scripts.Fornum', verbose_name='论坛')

    class Meta:
        db_table = 'user_fornum_rel'
        verbose_name = '用户论坛对应表'
        verbose_name_plural = verbose_name


class UserLogs(models.Model):
    """
        (1)用户id(用户外键)
        (2)登录ip
        (3)mac地址(可为空字段)
        (4)登录软件所属论坛的id(如果是登录后台管理系统则为-1)
        (5)登录时间
    """
    user = models.ForeignKey(to='User', verbose_name='用户外键')
    load_ip = models.CharField(max_length=50, verbose_name='用户IP登陆的地址')
    mac_add = models.CharField(max_length=50, verbose_name='用户登陆的mac地址', default='', blank=True)
    softwareType = models.IntegerField(verbose_name='软件所属论坛id')
    create_time = models.DateTimeField(auto_now=True, verbose_name='记录创建时间')

    class Meta:
        db_table = 'user_logs'
        verbose_name = '用户登陆信息表'
        verbose_name_plural = verbose_name