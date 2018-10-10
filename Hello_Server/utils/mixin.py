from django.contrib.auth.decorators import login_required, user_passes_test, REDIRECT_FIELD_NAME
from django.utils.decorators import classonlymethod
from django.views.generic import View
from django.conf import settings


class ValidatePermission(object):
    @classmethod
    def authenticated_func(cls, user):
        """检验权限的,函数,权限足够就返回True,后面再慢慢添加扩展不同权限
        user是request.user对象,即当前登录的用户对象

        只有 管理员,操作员,代理商,才能使用后台接口,广告主也不能使用后台的接口
        """
        return user.is_authenticated() and user.role < 4

    @classmethod
    def login_required(cls, function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
        """
        重写的login_required方法,用于更改权限管理
        """
        actual_decorator = user_passes_test(
            cls.authenticated_func,
            login_url=login_url,
            redirect_field_name=redirect_field_name
        )
        if function:
            return actual_decorator(function)
        return actual_decorator


class AdvertisersAuthority(ValidatePermission):
    """广告主登陆验证"""

    @classmethod
    def authenticated_func(cls, user):
        """检验权限的,函数,权限足够就返回True,后面再慢慢添加扩展不同权限
        user是request.user对象,即当前登录的用户对象

        登陆并且角色是广告主(代号为4)的时候才返回True
        """
        return user.is_authenticated() and user.role == 4


class AgentAuthority(ValidatePermission):
    """代理商登陆验证"""

    @classmethod
    def authenticated_func(cls, user):
        """检验权限的,函数,权限足够就返回True,后面再慢慢添加扩展不同权限
        user是request.user对象,即当前登录的用户对象

        登陆并且角色是代理商(代号为3)的时候才返回True
        """
        return user.is_authenticated() and user.role == 3


class OperatorAuthority(ValidatePermission):
    """操作员登陆验证"""

    @classmethod
    def authenticated_func(cls, user):
        """检验权限的,函数,权限足够就返回True,后面再慢慢添加扩展不同权限
        user是request.user对象,即当前登录的用户对象
        """
        return user.is_authenticated() and user.role < 3


class OnlyLoginRequireView(View):
    """只做登录校验的视图,不验证用户role"""

    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return login_required(view)

    def dispatch(self, request, *args, **kwargs):
        """
        分发请求方法函数
        :param request: 请求对象
        :param args:
        :param kwargs:
        :return:
        """
        # 分发之前先做一些其他的操作
        self.operate(request)

        if request.method.lower() in self.http_method_names:
            handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
        return handler(request, *args, **kwargs)

    def operate(self, request):
        """
        在这里做一些登陆后每个账户都会做的操作
        :param initkwargs:　视图初始化参数
        :return:　initkwargs
        """
        self.set_session_expiry(request)

    def set_session_expiry(self, request):
        request.session.set_expiry(settings.SESSION_EXPIRY_SECONDS)


class LoginRequireView(OnlyLoginRequireView):
    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return ValidatePermission.login_required(view)


class OperatorAuthorityView(OnlyLoginRequireView):
    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return OperatorAuthority.login_required(view)


class AgentAuthorityView(OnlyLoginRequireView):
    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return AgentAuthority.login_required(view)
