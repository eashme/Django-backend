from collections import Iterable
from django.conf import settings
from django.core.paginator import Paginator
from django.http import JsonResponse
from Hellocial_0_1.settings import logger
from apps.products.models import Program, Machine
from apps.scripts.models import Fornum
from apps.users.models import User, MemberShip
from utils.response_code import RET
from django.utils.timezone import datetime
from utils.mixin import LoginRequireView, OperatorAuthorityView, OnlyLoginRequireView
from utils.util_func import get_json_data, filter_null
import json,time


# Create your views here.

# /products/program
class ProgamView(OperatorAuthorityView):
    """程序管理视图
    只有后台操作员和管理员可以使用

    get请求 获取
    post请求 修改
    """

    def get(self, request):
        """
        查询字符串传了id参数就返回指定id的版本信息
        没传id,传了all参数就返回全部程序信息(不分页)
        没传id,也没传all参数,就返回分页的程序信息(page参数不传或者错误就返回第一页)
        """
        page = request.GET.get('page')
        f_id = request.GET.get('fornum_id')
        p_id = request.GET.get('id')
        is_all = request.GET.get('all')
        try:
            page = int(page)
        except TypeError:
            logger.debug('Page Error')
            page = 1
        if f_id is None and p_id is None:
            programs = Program.objects.all().order_by('-update_time')
        elif p_id is None and f_id is not None:
            try:
                fornum = Fornum.objects.get(id=f_id)
            except Fornum.DoesNotExist:
                logger.debug('Fornum Does Not Exist')
                return JsonResponse({'code': RET.PARAMERR, 'message': '论坛id参数错误'})
            programs = Program.objects.filter(fornum=fornum)
        else:
            programs = Program.objects.filter(id=p_id)

        pages = 1
        data_length = 0 if is_all is None and f_id is None else 1

        if len(programs) > 1:
            paginator = Paginator(programs, settings.PER_PAGE_COUNTS)
            pages = paginator.num_pages
            if page > pages:
                return JsonResponse({'code': RET.PARAMERR, 'message': '页码错误'})
            data_length = paginator.count
            programs_page = paginator.page(page)
        else:
            try:
                programs_page = [programs.first()]
            except Exception as e:
                logger.debug(e)
                return JsonResponse({'code': RET.PARAMERR, 'message': '没有该程序信息'})

        data = []

        if len(programs) == 0:
            programs_page = []

        if is_all is not None and f_id is None:
            programs_page = programs

        for program in programs_page:
            try:
                d = {
                    'id': program.id,
                    'title': program.title,
                    'fornum_name': program.fornum.fornum_name,
                    'fornum_id': program.fornum.id,
                    'version': program.version,
                    'is_active': program.is_active,
                    'description': program.description,
                    'join_date': program.create_time.strftime("%Y-%m-%d")
                }
            except Exception as e:
                logger.error(e)
                continue

            data.append(d)
        return JsonResponse({'code': RET.OK, 'message': '成功', 'data': data, 'pages': pages,
                             'data_length': data_length})

    def post(self, request):
        json_dict = get_json_data(request)
        p_id = request.GET.get('id')
        if json_dict is None:
            return JsonResponse({'code': RET.PARAMERR, 'message': '请使用json数据格式'})

        description = json_dict.get('description')
        fornum_id = json_dict.get('fornum_id')
        version = json_dict.get('version')
        title = json_dict.get('title')

        if not p_id:
            return JsonResponse({'code': RET.PARAMERR, 'message': '缺少必要参数'})

        if fornum_id:
            try:
                fornum = Fornum.objects.get(id=fornum_id)
            except Fornum.DoesNotExist:
                logger.debug('Fornum Does Not Exist')
                return JsonResponse({'code': RET.DBERR, 'message': '论坛不存在'})

        try:
            program = Program.objects.get(id=p_id)
            if description:
                program.description = description
            if title:
                program.title = title
            if version:
                program.version = version
            if fornum_id:
                program.fornum = fornum

            program.update_person = request.user.id
            program.update_time = datetime.now()

            program.save()

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RET.DBERR, 'message': '数据库错误,修改失败'})

        return JsonResponse({'code': RET.OK, 'message': '修改成功'})


# /products/program/vaildate
class CheckProgramView(OnlyLoginRequireView):
    """校验程序版本接口"""

    def get(self, request):
        """
        fornum_code     论坛编号
        p_version       程序版本号
        """
        fornum_code = request.GET.get('fornum_code')
        p_version = request.GET.get('p_version')

        if not all([fornum_code, p_version]):
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数错误'})

        try:
            fornum = Fornum.objects.get(title=fornum_code)
        except Exception as e:
            logger.debug(e)
            return JsonResponse({'code': RET.DBERR, 'message': '论坛编号不存在'})

        try:
            program = Program.objects.get(fornum=fornum, version=p_version)
        except Exception as e:
            logger.debug(e)
            return JsonResponse({'code': RET.PARAMERR, 'message': '程序版本号不存在'})
        try:
            data = {
                'title': program.title,
                'fornum_id': program.fornum.id,
                'fornum_name': program.fornum.fornum_name,
                'fornum_code': program.fornum.title,
                'version': program.version,
                'is_active': program.is_active,
                'description': program.description
            }
        except Exception as e:
            logger.error(e)
        return JsonResponse({'code': RET.OK, 'message': '获取程序信息成功', "data": data})


# /products/program/change
class ProgramChangeView(OperatorAuthorityView):
    """
    程序修改视图
    get请求　删除
    post请求　新增
    """

    def get(self, request):
        """
        通过QueryString传入所有要进行操作的id,键名为id,类型为int或数组
        op为操作标志为参数,也通过QueryString进行传入,该参数值如果为'ban'即为禁用操作,否则为删除操作
        :return:
        """

        # id 进行处理
        del_ids = request.GET.get('id')
        # 删除或者禁用操作
        operate = request.GET.get('op')

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

        programs = Program.objects.filter(id__in=del_ids)

        if len(programs) == 0:
            return JsonResponse({'code': RET.PARAMERR, 'message': '该id不存在'})

        if len(programs) != len(del_ids):
            logger.debug('{}程序id存在错误'.format(del_ids))
            return JsonResponse({'code': RET.PARAMERR, 'message': 'id存在错误'})

        if operate == "ban":
            # 如果是禁用操作
            for program in programs:
                program.is_active = not program.is_active
                program.save()
        else:
            for p in programs:
                p.is_delete = True
                p.save()

        return JsonResponse({'code': RET.OK, 'message': '操作成功'})

    def post(self, request):
        json_dict = get_json_data(request)
        if json_dict is None:
            return JsonResponse({'code': RET.PARAMERR, 'message': '请使用json数据格式'})

        description = json_dict.get('description')
        fornum_id = json_dict.get('fornum_id')
        version = json_dict.get('version')
        title = json_dict.get('title')

        if not all([version, fornum_id, title]):
            return JsonResponse({'code': RET.PARAMERR, 'message': '缺少必要参数'})

        if description is None: description = ''

        try:
            fornum = Fornum.objects.get(id=fornum_id)
        except Fornum.DoesNotExist:
            logger.debug('Fornum Does Not Exist')
            return JsonResponse({'code': RET.DBERR, 'message': '论坛不存在'})

        try:
            program = Program.objects.create(
                title=title,
                fornum=fornum,
                version=version,
                description=description,
                update_person=request.user.id,
                founder=request.user.id
            )
            program.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RET.DBERR, 'message': '数据库错误,创建失败'})

        return JsonResponse({'code': RET.OK, 'message': '成功'})


# /products/machine
class MachineView(OperatorAuthorityView):
    """
    get请求:  获取用户机器相关信息
    """

    def get(self, request):
        """
        查询字符串传了id参数就返回指定id的用户的机器信息
        没传id,传了all参数就返回全部程序信息(不分页)
        没传id,也没传all参数,就返回分页的程序信息(page参数不传或者错误就返回第一页)
        """
        page = request.GET.get('page')
        u_id = request.GET.get('id')
        is_all = request.GET.get('all')
        try:
            page = int(page)
        except TypeError:
            logger.debug('Page Error')
            page = 1

        if u_id is None:
            machines = Machine.objects.all().order_by('-create_time')
        else:
            try:
                user = User.objects.get(id=u_id)
                if user.role == 3:
                    # 代理商机器过滤,要显示它的子账户的机器登陆信息
                    slaves = MemberShip.objects.filter(master=user)
                    slaves = [slave.slave for slave in slaves]
                    slaves.append(user)
                    machines = Machine.objects.filter(user__in=slaves)
                else:
                    machines = Machine.objects.filter(user=user).order_by('-create_time')

            except User.DoesNotExist:
                logger.debug('User Does Not Exist')
                return JsonResponse({'code': RET.PARAMERR, 'message': '用户id参数有误'})

        pages = 1
        data_length = 0 if is_all is None and u_id is None else 1

        if len(machines) > 1:
            paginator = Paginator(machines, settings.PER_PAGE_COUNTS)
            pages = paginator.num_pages
            if page > pages:
                return JsonResponse({'code': RET.PARAMERR, 'message': '页码错误'})
            data_length = paginator.count
            machines_page = paginator.page(page)
        else:
            try:
                machines_page = [machines.first()]
            except Exception:
                logger.debug('Machine Does Not Exist')
                return JsonResponse({'code': RET.PARAMERR, 'message': '没有该机器信息'})

        data = []

        if len(machines) == 0:
            machines_page = []

        if is_all is not None and u_id is None:
            machines_page = machines

        for machine in machines_page:
            try:
                d = {
                    'id': machine.id,
                    'user_id': machine.user.id,
                    'user_name': machine.user.username,
                    'user_role': machine.user.role,
                    'mac_add': machine.mac_add,
                    'last_ip_add': machine.last_ip_add,
                    'last_login': machine.last_login.strftime("%Y-%m-%d %H:%M:%S"),
                    'is_active': machine.is_active
                }
            except Exception as e:
                logger.error(e)
                continue

            data.append(d)

        return JsonResponse({'code': RET.OK, 'message': '成功', 'data': data, 'pages': pages,
                             'data_length': data_length})


# /products/machine/change
class MachineChangeView(OperatorAuthorityView):
    """
    get请求:  删除或禁用用户机器相关信息
    """

    def get(self, request):

        """
        通过QueryString传入所有要进行操作的id,键名为id,类型为int或数组
        op为操作标志为参数,也通过QueryString进行传入,该参数值如果为'ban'即为禁用操作,否则为删除操作
        :return:
        """

        # id 进行处理
        del_ids = request.GET.get('id')
        # 删除或者禁用操作
        operate = request.GET.get('op')

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

        machines = Machine.objects.filter(id__in=del_ids)

        if len(machines) == 0:
            return JsonResponse({'code': RET.PARAMERR, 'message': '该id不存在'})

        if len(machines) != len(del_ids):
            return JsonResponse({'code': RET.PARAMERR, 'message': 'id存在错误'})

        if operate == "ban":
            try:
                # 如果是禁用操作
                for machine in machines:
                    machine.is_active = not machine.is_active
                    machine.save()
            except Exception as e:
                logger.error(e)
        else:
            for m in machines:
                m.is_delete = True
                m.save()

        return JsonResponse({'code': RET.OK, 'message': '操作成功'})
