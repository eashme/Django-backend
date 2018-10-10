from django.db import models


class DeactivateQuerySet(models.query.QuerySet):
    """
    自定义delete方法的查询集
    """
    def delete(self):
        self.deactivate()

    def deactivate(self):
        self.update(is_delete=True)


class BaseManager(models.Manager):
    def get_query_set(self):
        return models.query.QuerySet(self.model, using=self._db)

    def delete(self):
        self.get_query_set().delete()

    def all(self):
        return self.get_query_set().filter(is_delete=False)

    def filter(self, *args, **kwargs):
        return self.get_query_set().filter(*args, **kwargs).filter(is_delete=False)


class BaseModel(models.Model):
    """抽象模型基类"""
    create_time = models.DateField(auto_now_add=True, verbose_name='创建时间')
    founder = models.IntegerField(verbose_name='创建人', null=True, default=-1)

    update_time = models.DateField(auto_now=True, verbose_name='更新时间')
    update_person = models.IntegerField(verbose_name='更新人', null=True, default=-1)

    is_delete = models.BooleanField(default=False, verbose_name='删除标记')

    objects = BaseManager()

    class Meta:
        """指定这是一个抽象模型基类"""
        abstract = True
