from django.views.generic import View
from django.http import JsonResponse
from utils.response_code import RET
from django.contrib.auth.hashers import make_password
from django.utils.timezone import now

class RedirctView(View):
    """重定向视图"""

    def get(self, request):
        return JsonResponse({
            'code': RET.USERERR,
            'message': "账户问题,请登陆或更换有效账号"
        })

    def post(self, request):
        return JsonResponse({
            'code': RET.USERERR,
            'message': "账户问题,请登陆或更换有效账号"
        })


# /isLogin
class CheckLoginView(View):
    def get(self, request):
        if request.user.is_authenticated():
            return JsonResponse({'code': RET.OK, 'message': '已登录', 'user_role': request.user.role,'user_name':request.user.username})
        else:
            return JsonResponse({'code': RET.USERERR, 'message': '未登录'})


class ServiceDatetimeView(View):
    """服务器时间接口"""
    def get(self,reuqest):
        return JsonResponse({'code':RET.OK,'datetime':now().strftime("%Y-%m-%d %H:%M:%S")})
