import json,time
from collections import Iterable
from django.utils.timezone import datetime
from django.conf import settings
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.generic import View
from Hellocial_0_1.settings import logger
from apps.products.models import Program
from apps.users.models import UserFornumRelation
from utils.mixin import LoginRequireView, OperatorAuthorityView
from utils.response_code import RET
from apps.scripts.models import JavaScriptCode, Fornum
from utils.util_func import get_json_data, filter_null
from utils.captcha_recognition import DoubanCaptchaRecognition,RuoKuaiCaptcha,CaptchaRecognition

# Create your views here.


# /script/fornum
class ForumView(OperatorAuthorityView):
    """
    get请求 获取 论坛相关数据
    post请求 修改 论坛相关数据
    """

    def get(self, request):

        page = request.GET.get('page')
        f_id = request.GET.get('id')
        is_all = request.GET.get('all')
        try:
            page = int(page)
        except TypeError:
            logger.debug('页码错误')
            page = 1
        if f_id is None:
            fornums = Fornum.objects.all().order_by('-update_time')
        else:
            fornums = Fornum.objects.filter(id=f_id)

        pages = 1
        data_length = 0 if is_all is None and f_id is None else 1

        if len(fornums) > 1:
            paginator = Paginator(fornums, settings.PER_PAGE_COUNTS)
            pages = paginator.num_pages
            if page > pages:
                page = 1
            data_length = paginator.count
            fornums_page = paginator.page(page)
        else:
            try:
                fornums_page = [fornums.first()]
            except Exception:
                logger.info('没有该论坛信息')
                return JsonResponse({'code': RET.PARAMERR, 'message': '没有该论坛信息'})

        data = []

        if len(fornums) == 0:
            fornums_page = []

        if is_all is not None and f_id is None:
            fornums_page = fornums

        for fornum in fornums_page:
            d = {
                'id': fornum.id,
                'title': fornum.title,
                'fornum_name': fornum.fornum_name,
                'description': fornum.description,
                'app_type':fornum.app_type
            }

            data.append(d)

        return JsonResponse({'code': RET.OK, 'message': '成功', 'data': data, 'pages': pages,
                             'data_length': data_length})

    def post(self, request):
        f_id = request.GET.get('id')
        json_dict = get_json_data(request)
        if json_dict is None:
            return JsonResponse({'code': RET.PARAMERR, 'message': '请使用json数据格式'})

        if f_id is None:
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数错误'})

        description = json_dict.get('description')
        title = json_dict.get('title')
        app_type = json_dict.get('app_type')

        try:
            fornum = Fornum.objects.get(id=f_id)
            if title:
                fornum.title = title
            if description:
                fornum.description = description
            if app_type:
                if int(app_type) not in Fornum.APP_TYPE.keys():
                    return JsonResponse({'code':RET.PARAMERR,'message':'应用类型错误'})
                fornum.app_type = app_type

            fornum.update_person = request.user.id
            fornum.update_time = datetime.now()
            fornum.save()
        except Exception as e:
            logger.warn(e)
            return JsonResponse({'code': RET.PARAMERR, 'message': '该论坛不存在'})

        return JsonResponse({'code': RET.OK, 'message': '修改成功'})


# /script/forum/change
class ForumChangeView(OperatorAuthorityView):
    """
    get删除论坛相关信息
    post增加论坛数据
    """

    def get(self, request):
        del_ids = request.GET.get('id')

        if del_ids is None:
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数错误'})

        try:
            del_ids = json.loads(del_ids)
        except Exception as e:
            logger.debug(e)
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数错误'})

        # 非可迭代对象和字符串把其变成单元素的列表
        if (not isinstance(del_ids, Iterable)) or isinstance(del_ids, str):
            del_ids = [del_ids]

        # 过滤掉非整形数据
        del_ids = list(filter(filter_null, del_ids))

        if len(del_ids) == 0:
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数错误'})

        fornums = Fornum.objects.filter(id__in=del_ids)

        if len(fornums) == 0:
            return JsonResponse({'code': RET.PARAMERR, 'message': '该id不存在'})

        if len(fornums) != len(del_ids):
            logger.debug('id存在错误')
            return JsonResponse({'code': RET.PARAMERR, 'message': 'id存在错误'})

        # 删除该论坛的js代码
        for fornum in fornums:
            for p in Program.objects.filter(fornum=fornum):
                p.is_delete = True
                p.save()

            UserFornumRelation.objects.filter(fornum=fornum).delete()

            for j in JavaScriptCode.objects.filter(fornum=fornum):
                j.is_delete = True
                j.save()

            fornum.is_delete = True
            fornum.save()

        return JsonResponse({'code': RET.OK, 'message': '删除成功'})

    def post(self, request):
        json_dict = get_json_data(request)
        if json_dict is None:
            return JsonResponse({'code': RET.PARAMERR, 'message': '请使用json数据格式'})

        description = json_dict.get('description')
        fornum_name = json_dict.get('fornum_name')
        title = json_dict.get('title')
        app_type = json_dict.get('app_type')

        if description is None: description = ''
        if title is None : title = ''
        if app_type is None: app_type = 0

        if fornum_name is None:
            return JsonResponse({'code': RET.PARAMERR, 'message': '缺少必要参数'})
        try:
            if int(app_type) not in Fornum.APP_TYPE.keys():
                return JsonResponse({'code': RET.PARAMERR, 'message': '应用类型错误'})
        except Exception:
            return JsonResponse({'code': RET.PARAMERR, 'message': '应用类型错误'})

        try:
            fornum = Fornum.objects.create(
                title = title,
                fornum_name=fornum_name,
                description=description,
                update_person=request.user.id,
                founder=request.user.id,
                app_type=app_type
            )
            fornum.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RET.DBERR, 'message': '数据库错误,创建失败'})

        return JsonResponse({'code': RET.OK, 'message': '成功'})


# /script/js
class JavaScriptCodeView(OperatorAuthorityView):
    """
    get 获取js脚本信息
    post 修改js脚本信息
    """

    def get(self, request):
        """
        只传了all参数就返回所有的js脚本记录,不做分页
        传了js_id就只返回单独该id对应的js记录
        传了fornum_id,并且没传js_id就返回该论坛对应的所有js记录,分页显示
        page代表分页的页数,在获取对应论坛的js记录时需要传,不然返回第一页

        :param request:
        :return:
        """
        page = request.GET.get('page')
        f_id = request.GET.get('fornum_id')
        js_id = request.GET.get('js_id')

        try:
            page = int(page)
        except TypeError:
            logger.debug('page error')
            page = 1

        try:
            js_id = int(js_id)
        except Exception:
            js_id = None
        try:
            f_id = int(f_id)
        except Exception:
            f_id = None

        if js_id is None and f_id is not None:
            try:
                fornum = Fornum.objects.get(id=f_id)
            except Exception:
                logger.debug('id 为{}的论坛不存在'.format(f_id))
                return JsonResponse({'code': RET.PARAMERR, 'message': '论坛不存在'})

            js_codes = JavaScriptCode.objects.filter(fornum=fornum).order_by('-update_time')
        elif not all([js_id,f_id]):
            js_codes = JavaScriptCode.objects.all()

        else:
            js_codes = JavaScriptCode.objects.filter(id=js_id)

        pages = 1
        data_length = 0 if js_id is None and f_id is None else 1

        if len(js_codes) > 1:
            paginator = Paginator(js_codes, settings.PER_PAGE_COUNTS)
            pages = paginator.num_pages
            if page > pages:
                page = 1
            data_length = paginator.count
            js_code_page = paginator.page(page)
        else:
            try:
                js_code_page = [js_codes.first()]
            except Exception as e:
                logger.debug(e)
                return JsonResponse({'code': RET.PARAMERR, 'message': '没有该论坛信息'})

        data = []

        if len(js_codes) == 0:
            js_code_page = []


        for js in js_code_page:
            d = {
                'id': js.id,
                'title': js.title,
                'description': js.description,
                'fornum': js.fornum.fornum_name,
                'js_code': js.js_code,
                'fornum_id':js.fornum.id
            }

            data.append(d)

        return JsonResponse({'code': RET.OK, 'message': '成功', 'data': data, 'pages': pages,
                             'data_length': data_length})

    def post(self, request):
        json_dict = get_json_data(request)

        j_id = request.GET.get('id')
        js_code = json_dict.get('js_code')
        description = json_dict.get('description')
        fornum_id = json_dict.get('fornum_id')

        description = '' if description is None else description

        if not all([j_id, js_code, fornum_id]):
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数错误'})

        try:
            js = JavaScriptCode.objects.get(id=int(j_id))
        except Exception as e:
            logger.debug(e)
            return JsonResponse({'code': RET.PARAMERR, 'message': 'ID存在错误'})

        try:
            fornum = Fornum.objects.get(id=int(fornum_id))
        except Exception as e:
            logger.debug(e)
            return JsonResponse({'code': RET.DBERR, 'message': '指定修改的论坛错误'})

        try:
            js.description = description
            js.fornum = fornum
            js.js_code = js_code
            js.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RET.DBERR, 'message': '数据库错误'})

        return JsonResponse({'code': RET.OK, 'message': '成功'})


# /script/js/change
class JavaScriptCodeChangeView(OperatorAuthorityView):
    """
    get: 删除js脚本相关信息
    post: 增加js脚本信息
    """

    def get(self, request):
        d_id = request.GET.get('id')

        if d_id is None:
            return JsonResponse({'code': RET.PARAMERR, 'message': '缺少必要参数'})

        try:
            d_id = json.loads(d_id)
        except Exception:
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数错误'})

        # 不是可迭代对象
        if not isinstance(d_id, Iterable) or isinstance(d_id, str):
            d_id = [d_id]

        # 将不能转换为整型的过滤掉
        d_id = list(filter(filter_null, d_id))

        if len(d_id) == 0:
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数错误'})

        js = JavaScriptCode.objects.filter(id__in=d_id).all()

        if len(js) != len(d_id):
            logger.debug('js脚本{}存在错误'.format(d_id))
            return JsonResponse({'code': RET.PARAMERR, 'message': '传入的参数有误'})

        try:
            for j in js:
                j.is_delete = True
                j.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RET.DBERR, 'message': '数据库错误,删除失败'})

        return JsonResponse({'code': RET.OK, 'message': '删除成功'})

    def post(self, request):
        json_dict = get_json_data(request)
        if json_dict is None:
            return JsonResponse({'code': RET.PARAMERR, 'message': '请使用json数据格式'})

        js_code = json_dict.get('js_code')
        fornum_id = json_dict.get('fornum_id')
        title = json_dict.get('title')
        description = json_dict.get('description')

        if not all([js_code, fornum_id, title]):
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数错误'})

        # 默认值设置为''
        description = '' if description is None else description

        try:
            fornum = Fornum.objects.get(id=fornum_id)
        except Exception as e:
            logger.debug(e)
            return JsonResponse({'code': RET.DBERR, 'message': '论坛不存在'})

        try:
            js = JavaScriptCode.objects.create(
                fornum=fornum,
                js_code=js_code,
                title=title,
                description=description,
                update_person=request.user.id,
                founder=request.user.id,
            )

            js.save()

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RET.DBERR, 'message': '添加js代码失败'})

        return JsonResponse({'code': RET.OK, 'message': '添加成功'})


# /script/captcha
class CaptchaView(View):
    def post(self,request):
        """
        使用post请求以json格式传入数据
        1.若快平台      用户账户
        2.若快平台      用户密码
        3.论坛编号      验证码所属的论坛的编号
        4.验证码类型    {0:未知,1:中文,2:英文,3:数字,4:英文数字混合}
        5.图片验证码的完整url

        验证码类型未知的话 服务端将无法对图片做任何处理,发送至打码平台将准确率极低

        :param request:
        :return:
        """
        json_dict = get_json_data(request)
        if not json_dict:
            return JsonResponse({'code':RET.PARAMERR,'message':'请使用json格式数据'})

        image_url = json_dict.get('img_url')
        rk_username = json_dict.get('rk_username')
        rk_password = json_dict.get('rk_password')
        fornum_code = json_dict.get('fornum_code')
        captcha_type = json_dict.get('captcha_type')

        if not all([image_url,rk_username,rk_password,fornum_code]):
            return JsonResponse({'code':RET.PARAMERR,'message':'参数错误'})

        captcha_type = captcha_type if captcha_type else 0

        try:
            captcha_type = int(captcha_type)
            if captcha_type > 4:
                raise Exception('非法验证码类型参数')
        except Exception:
            logger.debug('Params Error')
            return JsonResponse({'code':RET.PARAMERR,'message':'参数错误'})

        if len(rk_password) != 32:
            return JsonResponse({'code':RET.PARAMERR,'message':'密码需要32位小写md5加密传输'})

        try:
            fornum = Fornum.objects.get(title=fornum_code)
        except Fornum.DoesNotExist:
            logger.debug('论坛编号错误')
            return JsonResponse({'code':RET.PARAMERR,'message':'论坛编号错误'})


        if fornum.id == 4:
            # 是豆瓣的
            image_engine = DoubanCaptchaRecognition()

        else:
            return JsonResponse({'code':RET.SERVERERR,'message':'暂不支持豆瓣以外论坛的验证码识别'})

        im = image_engine.get_image_obj(image_url)

        if captcha_type == 1:
            # 处理中文验证码
            im = image_engine.process_chinese(im)
        elif captcha_type == 2:
            # 处理英文验证码
            im = image_engine.process_english(im)

        sender = RuoKuaiCaptcha(username=rk_username,password=rk_password)

        captcha_type = settings.RUOKUAI_CAPTCHA_TYPE[captcha_type]

        return JsonResponse(sender.get_string(im,im_type=captcha_type))

