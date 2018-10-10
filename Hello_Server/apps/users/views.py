from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.generic import View
from apps.scripts.models import Fornum
from utils.response_code import RET
from apps.users.models import User, MemberShip, UserInfo, UserFornumRelation, UserLogs
from apps.products.models import Machine
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.hashers import make_password
from utils.captcha import Captcha
from django_redis import get_redis_connection
from django.conf import settings
from utils.mixin import LoginRequireView, OnlyLoginRequireView
from utils.util_func import get_json_data, filter_null, getIPFromDJangoRequest
from django.utils.timezone import datetime
from datetime import timedelta
import hashlib, json, time
from collections import Iterable
from django.db import transaction, models
from Hellocial_0_1.settings import logger



# Create your views here.

# /users
class UserInfoView(OnlyLoginRequireView):
    """当前用户信息视图"""

    def get(self, request):
        """获取当前或传入用户id的详细信息

        如果传入用户id,则返回对应id的详细信息
        如果不传用户id就返回当前用户的详细信息
        """
        id = request.GET.get('id')
        if id is None:
            user = request.user
        else:
            try:
                user = User.objects.get(id=id)
                if user.is_delete:
                    raise User.DoesNotExist
            except Exception as e:
                logger.debug(e)
                return JsonResponse({'code': RET.OK, 'message': '不存在该用户'})

        if user.is_delete:
            return JsonResponse({'code': RET.OK, 'message': '不存在该用户'})
        try:
            user_info = UserInfo.objects.get(user=user)
            mem_info = MemberShip.objects.get(slave=user)
        except Exception:
            end_time = -1
            valid_days = -1
            phone = -1
            gender = 1
            accounts = -1
            remarks = ''
            role = 1
        else:
            end_time = mem_info.end_time.strftime("%Y-%m-%d %H:%M:%S")
            valid_days = (mem_info.end_time - datetime.now()).days

            role = user.role
            phone = user_info.telephone
            gender = user_info.gender
            accounts = user_info.accounts
            remarks = user_info.remarks

        # 论坛信息展示
        ufrs = UserFornumRelation.objects.filter(user=user).all()
        u_fornums = []
        for ufr in ufrs:
            f = {
                'fornum_name': ufr.fornum.fornum_name,
                'fornum_id': ufr.fornum.id,
                'fornum_code': ufr.fornum.title,
                'app_type':ufr.fornum.app_type
            }
            u_fornums.append(f)
        # 父级账户信息展示
        try:
            mem = MemberShip.objects.get(slave=user)
            parent_name = mem.master.name
            parent_id = mem.master.id
            parent_role = mem.master.role
        except MemberShip.DoesNotExist:
            parent_name = ''
            parent_id = -1
            parent_role = -1

        data = {
            'parent_role': parent_role,
            'parent_name': parent_name,
            'parent_id': parent_id,
            'id': user.id,
            'role': role,
            'phone': phone,
            'gender': gender,
            'accounts': accounts,
            'remarks': remarks,
            'end_time': end_time,
            'valid_days': valid_days,
            'email': user.email,
            'username': user.username,
            'name': user.name,
            'fornums': u_fornums
        }
        try:
            data['last_join'] = user.last_login.strftime("%Y-%m-%d %H:%M:%S"),
        except Exception as e:
            logger.debug(e)
            data['last_join'] = None

        return JsonResponse({"code": RET.OK, "data": data, 'message': '成功'})

    def post(self, request):
        """
        通过用户role获取用户信息
        post方式,Json格式传递
        role参数,可为数组或int类型,数组类型为多个角色
        """
        page = request.GET.get('page')
        json_dict = get_json_data(request)
        if json_dict is None:
            return JsonResponse({'code': RET.PARAMERR, 'message': '请使用json格式数据'})

        role = json_dict.get('role')

        if request.user.role < 2:

            if not role:
                return JsonResponse({'code': RET.PARAMERR, 'message': '缺少必要参数'})

            if not isinstance(role, Iterable) or isinstance(role, str):
                role = [role]

            role = list(filter(filter_null, role))
            role = [int(i) for i in role]

            if not role:
                return JsonResponse({'code': RET.PARAMERR, 'message': '参数错误'})

            users = User.objects.filter(role__in=role).order_by('-is_active', '-date_joined')
        else:
            mems = MemberShip.objects.filter(master=request.user)
            users = [mem.slave for mem in mems]

        try:
            page = int(page)
        except TypeError:
            logger.info('页码错误')
            page = 1

        # 每页10条数据
        paginator = Paginator(users, settings.PER_PAGE_COUNTS)

        if (page > paginator.num_pages) or (page < 0):
            page = 1

        users = paginator.page(page)

        data = []

        for user in users:

            if user.is_delete:
                continue

            # 论坛信息展示
            ufrs = UserFornumRelation.objects.filter(user=user)
            u_fornums = []
            for ufr in ufrs:
                f = {
                    'fornum_name': ufr.fornum.fornum_name,
                    'fornum_id': ufr.fornum.id,
                    'fornum_code': ufr.fornum.title,
                    'app_type':ufr.fornum.app_type,
                }
                u_fornums.append(f)

            try:
                mem_info = MemberShip.objects.get(slave=user)
            except Exception:
                remain_days = -1
                end_date = -1
            else:
                remain_days = (mem_info.end_time - datetime.now()).days
                end_date = mem_info.end_time.strftime("%Y年%m月%d日 %H:%M")
                remain_days = remain_days if remain_days >= 0 else -1

            # 父级账户信息展示
            try:
                mem = MemberShip.objects.get(slave=user)
                parent_name = mem.master.name
                parent_id = mem.master.id
                parent_role = mem.master.role
                remarks = user.userinfo_set.first().remarks
            except MemberShip.DoesNotExist:
                logger.info('%d缺少隶属关系' % user.id)
                parent_name = ''
                parent_id = -1
                parent_role = -1
                remarks = ''
            try:
                d = {
                    'parent_role': parent_role,
                    'parent_name': parent_name,
                    'parent_id': parent_id,
                    'id': user.id,
                    'username': user.username,
                    'name': user.name,
                    'email': user.email,
                    'role': user.role,
                    'remarks': remarks,
                    'remain_days': remain_days,
                    'join_date': user.date_joined.strftime("%Y年%m月%d日 %H:%M"),
                    'end_date': end_date,
                    'is_in_use': user.is_active,
                    'fornums': u_fornums
                }
            except Exception as e:
                logger.error(e)
                continue

            data.append(d)

        return JsonResponse({'code': RET.OK, 'message': '成功', 'data': data, 'pages': paginator.num_pages,
                             'data_length': paginator.count})


# /users/relations
class UserRelationView(LoginRequireView):
    """
    获取从属信息视图
    """

    def get(self, request):
        # 获取页码
        page = request.GET.get('page')

        if request.user.role in [3, 4]:
            relations = MemberShip.objects.filter(master=request.user).order_by('-slave__is_active',
                                                                                '-slave__date_joined')
        else:
            relations = MemberShip.objects.exclude(slave=request.user).order_by('-slave__is_active',
                                                                                '-slave__date_joined')

        try:
            page = int(page)
            logger.debug('页码错误')
        except TypeError:
            page = 1

        # 每页10条数据
        paginator = Paginator(relations, settings.PER_PAGE_COUNTS)

        if (page > paginator.num_pages) or (page < 0):
            page = 1

        rel_page = paginator.page(page)

        data = []
        for rel in rel_page:
            if rel.slave.is_delete:
                continue

            days = (rel.end_time - datetime.now()).days
            # 如果为负数
            days = days if days >= 0 else -1
            can_use = '可用' if days != -1 else '不可用'
            # 论坛信息展示
            ufrs = UserFornumRelation.objects.filter(user=rel.slave)
            u_fornums = []
            for ufr in ufrs:
                f = {
                    'fornum_name': ufr.fornum.fornum_name,
                    'fornum_id': ufr.fornum.id,
                    'fornum_code': ufr.fornum.title,
                    'app_type':ufr.fornum.app_type
                }
                u_fornums.append(f)

            try:
                d = {
                    'parent_role': rel.master.role,
                    'parent_name': rel.master.name,
                    'parent_id': rel.master.id,
                    'slave_name': rel.slave.name,
                    'slave_username': rel.slave.username,
                    'slave_id': rel.slave.id,
                    'role': rel.slave.role,
                    'create_time': rel.create_time,
                    'remarks': rel.slave.userinfo_set.first().remarks,
                    'update_time': rel.update_time,
                    'end_time': rel.end_time.strftime("%Y年%m月%d日 %H:%M"),
                    'remain_days': days,
                    'can_use': can_use,
                    'fornums': u_fornums
                }
            except Exception as e:
                logger.error(e)
                continue
            data.append(d)

        return JsonResponse({'code': RET.OK, 'message': '成功', 'data': data, 'pages': paginator.num_pages,
                             'data_length': paginator.count})


# /users/slaves
class UserSlaveView(LoginRequireView):
    def get(self, request):
        page = request.GET.get('page')

        # 代理商和广告主只能处理自己的隶属账户
        if request.user.role in [3, 4]:
            slaves = MemberShip.objects.filter(master=request.user).order_by('-slave__is_active', '-slave__date_joined')
        else:
            slaves = MemberShip.objects.all().order_by('-slave__is_active', '-slave__date_joined')

        try:
            page = int(page)
        except TypeError:
            page = 1

        # 每页10条数据
        paginator = Paginator(slaves, settings.PER_PAGE_COUNTS)

        if (page > paginator.num_pages) or (page < 0):
            page = 1

        rel_page = paginator.page(page)

        data = []
        for slave in rel_page:
            if slave.slave.is_delete:
                continue

            remain_days = (slave.end_time - datetime.now()).days
            remain_days = remain_days if remain_days >= 0 else -1
            # 论坛信息展示
            ufrs = UserFornumRelation.objects.filter(user=slave.slave)
            u_fornums = []
            for ufr in ufrs:
                f = {
                    'fornum_name': ufr.fornum.fornum_name,
                    'fornum_id': ufr.fornum.id,
                    'fornum_code': ufr.fornum.title,
                    'app_type':ufr.fornum.app_type
                }
                u_fornums.append(f)

            try:
                d = {
                    'parent_role': slave.master.role,
                    'parent_name': slave.master.name,
                    'parent_id': slave.master.id,
                    'id': slave.slave.id,
                    'username': slave.slave.username,
                    'name': slave.slave.name,
                    'email': slave.slave.email,
                    'role': slave.slave.role,
                    'remarks': slave.slave.userinfo_set.first().remarks,
                    'remain_days': remain_days,
                    'join_date': slave.slave.date_joined.strftime("%Y年%m月%d日 %H:%M"),
                    'end_date': slave.end_time.strftime("%Y年%m月%d日 %H:%M"),
                    'is_in_use': slave.slave.is_active,
                    'fornums': u_fornums
                }
            except Exception as e:
                logger.error(e)
                continue
            data.append(d)

        # 按剩余使用天数排序
        return JsonResponse({'code': RET.OK, 'message': '成功', 'data': data, 'pages': paginator.num_pages,
                             'data_length': paginator.count})


# /users/slaves/remove
class UserSlaveDelView(LoginRequireView):
    def get(self, request):
        """禁用接口"""

        ban_ids = request.GET.get('id')

        if not all([ban_ids]):
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数错误'})

        try:
            ban_ids = json.loads(ban_ids)
        except Exception:
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数错误'})

        # 非可迭代对象和字符串把其变成单元素的列表
        if (not isinstance(ban_ids, Iterable)) or isinstance(ban_ids, str):
            ban_ids = [ban_ids]

        # 过滤掉非整形数据
        ban_ids = list(filter(filter_null, ban_ids))

        if len(ban_ids) == 0:
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数错误'})

        try:
            users = User.objects.filter(id__in=ban_ids)
            if len(users) != len(ban_ids):
                return JsonResponse({'code': RET.PARAMERR, 'message': '存在错误id参数'})

            # 校验广告主和代理商的禁用操作权限
            if request.user.role in [3, 4]:
                slaves = [u.slave for u in MemberShip.objects.filter(master=request.user)]
                users = list(filter(lambda x: x in slaves, users))

                if len(users) != len(ban_ids):
                    logger.info('{}中有无效的id'.format(ban_ids))
                    return JsonResponse({'code': RET.PARAMERR, 'message': '禁用失败,无法禁用他人的隶属账户'})

            for user in users:
                user.is_active = not user.is_active
                user.save()
        except Exception as e:
            logger.warning(e)
            return JsonResponse({'code': RET.DBERR, 'message': '数据库错误'})

        return JsonResponse({'code': RET.OK, 'message': '成功'})

    def post(self, request):
        """删除接口"""
        json_dict = get_json_data(request)
        if json_dict is None:
            return JsonResponse({'code': RET.PARAMERR, 'message': '请使用json格式数据'})

        if request.user.role > 2:
            return JsonResponse({'code': RET.USERERR, 'message': '您没有删除账号的权限'})

        del_ids = json_dict.get('id')

        if del_ids is None:
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数错误'})

        # 删除单个拿到的id是单独的一个字符串,将其变成列表用in删除s
        if (not isinstance(del_ids, Iterable)) or isinstance(del_ids, str):
            del_ids = [del_ids]

        # 过滤掉非整形数据
        del_ids = list(filter(filter_null, del_ids))

        if len(del_ids) == 0:
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数错误'})

        users = User.objects.filter(id__in=del_ids)

        if len(users) != len(del_ids):
            logger.info('{}中参数存在错误'.format(del_ids))
            return JsonResponse({'code': RET.DBERR, 'message': 'id存在错误,删除失败'})

        # 校验广告主和代理商的删除操作权限
        if request.user.role in [3, 4]:
            slaves = [u.slave for u in MemberShip.objects.filter(master=request.user)]
            users = list(filter(lambda x: x in slaves, users))

            if len(users) != len(del_ids):
                logger.warning('存在越权删除现象,可能接口正在被攻击')
                return JsonResponse({'code': RET.PARAMERR, 'message': '删除失败,无法删除他人的隶属账户'})

        operators = [user for user in users if user.role < 3]

        if operators and request.user.role > 1:
            return JsonResponse({'code': RET.USERERR, 'message': '没有删除同事的权限'})

        remove_users = [user for user in users]

        # 代理商账户删除一切相关账户,管理员账户不删相关账户
        users = [user for user in users if user.role > 2]

        while True:
            # 循环搜索要删除的层级用户
            mems = MemberShip.objects.filter(master__in=users)
            if len(mems) < 1: break
            slaves = [mem.slave for mem in mems]
            for mem in mems:
                mem.is_delete = True
                mem.save()
            remove_users += slaves
            users = slaves

        for m in MemberShip.objects.filter(slave__in=remove_users):
            m.is_delete = True
            m.save()
        for m in Machine.objects.filter(user__in=remove_users):
            m.is_delete = True
            m.save()
        UserFornumRelation.objects.filter(user__in=remove_users).delete()

        for ui in UserInfo.objects.filter(user__in=remove_users):
            ui.is_delete = True
            ui.save()

        for user in remove_users:
            user.is_delete = True
            user.save()

        return JsonResponse({'code': RET.OK, 'message': '删除成功'})


# /users/edit
class UserSlaveEditView(LoginRequireView):
    def post(self, request):
        u_id = request.GET.get('id')
        json_dict = get_json_data(request)
        if json_dict is None:
            return JsonResponse({'code': RET.PARAMERR, 'message': '请使用json格式数据'})

        password = json_dict.get('password')
        email = json_dict.get('email')
        role = json_dict.get('adminRole')
        gender = json_dict.get('sex')
        remarks = json_dict.get('remarks')
        telephone = json_dict.get('phone')
        accounts = json_dict.get('accounts')
        end_time = json_dict.get('end_time')
        fornum_id = json_dict.get('fornum_id')
        name = json_dict.get('name')

        if not all([role, u_id]):
            return JsonResponse({"code": RET.PARAMERR, 'message': '参数错误'})

        # 是否修改密码的标志位
        is_update_password = not (password == '' or password is None)

        # 如果密码传过来没有做md5加密
        if is_update_password and len(password) != 32:
            logger.warning('密码没有md5加密传输')
            encoder = hashlib.md5()
            encoder.update(password.encode(encoding='utf-8'))
            password = password.hexdigest().lower()

        if accounts is None:
            accounts = 0

        try:
            gender = int(gender)
        except Exception:
            gender = 0
        # 校验数字类型参数
        try:
            role = int(role)
            accounts = int(accounts)
        except Exception as e:
            logger.debug(e)
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数类型错误'})

        if role > 6 or role < 1:
            logger.warning('用户要修改的role不合法')
            return JsonResponse({'code': RET.PARAMERR, 'message': '身份不合法'})

        try:
            # 转换为时间为python日期类型对象
            end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        except Exception:
            logger.warning('修改的日期时间不合法')
            end_time = datetime.now() + timedelta(hours=settings.ACCOUNTS_VALID_HOURS)

        try:
            user = User.objects.get(id=u_id)
        except Exception as e:
            logger.warning(e)
            return JsonResponse({'code': RET.DBERR, 'message': '修改用户不存在'})

        is_alert_fornum = False

        if request.user.role in [1, 2]:
            is_alert_fornum = True
        # 代理商
        if request.user.role == 3:
            if user.id == request.user.id:
                # 改自己的
                role = 3
            else:
                is_alert_fornum = True
                role = 6

            accounts = 0

        # 广告主
        if request.user.role == 4:
            if user.id == request.user.id:
                # 改自己的,不能该身份,所以身份不变
                role = 4
            else:
                is_alert_fornum = True
                role = 5

            accounts = 0

            try:
                # 广告主设置的有效期不能大于自己的有效期
                self_end_time = MemberShip.objects.get(slave=request.user).end_time
                end_time = self_end_time if end_time > self_end_time else end_time
            except Exception as e:
                logger.error(e)
                return JsonResponse({'code': RET.DBERR, 'message': '数据库错误'})

        # 可以修改论坛,并且传入了要修改的论坛的id值
        if fornum_id and is_alert_fornum:
            if not isinstance(fornum_id, Iterable) or isinstance(fornum_id, str):
                fornum_id = [fornum_id]

            try:
                fornum_id = list(filter(filter_null, fornum_id))
                fornum_id = [int(i) for i in fornum_id]
            except Exception:
                return JsonResponse({'code': RET.PARAMERR, 'message': '用户论坛相关参数错误'})

            if len(fornum_id) == 0:
                return JsonResponse({'code': RET.PARAMERR, 'message': '用户论坛相关参数错误'})

            uf_rels = UserFornumRelation.objects.filter(user=user).all()

            uf_f_ids = [uf_rel.fornum.id for uf_rel in uf_rels]

            if uf_f_ids != fornum_id:
                # 改前和改后一致,不做修改,否则要修改

                # 旧的不在新的里就是要删除的
                del_cols = [i for i in uf_f_ids if i not in fornum_id]
                # 新的不在旧的里就是要创建的
                create_cols = [i for i in fornum_id if i not in uf_f_ids]

                if request.user.role > 2:

                    f_ids = [i.fornum.id for i in UserFornumRelation.objects.filter(user=request.user).all()]

                    for c in create_cols:
                        if c not in f_ids:
                            return JsonResponse({'code': RET.PARAMERR, 'message': '论坛相关参数错误'})

                try:
                    with transaction.atomic():
                        # 删除
                        uf_rels.filter(fornum_id__in=del_cols).delete()

                        # 新增
                        for i in create_cols:
                            try:
                                fornum = Fornum.objects.get(id=i)
                            except Fornum.DoesNotExist:
                                logger.warning('论坛id错误')
                                return JsonResponse({'code': RET.PARAMERR, 'message': '论坛id错误'})

                            new_uf_rel = UserFornumRelation.objects.create(
                                user=user,
                                fornum=fornum,
                                founder=request.user.id,
                                update_person=request.user.id,
                                update_time=datetime.now()
                            )
                            new_uf_rel.save()

                except Exception as e:
                    logger.error(e)
                    return JsonResponse({'code': RET.DBERR, 'message': '数据库错误,用户论坛修改失败'})

        try:
            # 　超级用户可能没有以下两张表的数据的
            user_info = UserInfo.objects.get(user=user)

            if request.user.role in [3, 4] and user.id != request.user.id:
                try:
                    mem = MemberShip.objects.get(master=request.user, slave=user)
                except Exception:
                    logger.warning('用户修改了非自己的从属账户,修改人id为%d' % request.user.id)
                    return JsonResponse({'code': RET.USERERR, "message": "只能修改自己的从属账户"})
            else:
                mem = MemberShip.objects.get(slave=user)

            user_info.update_time = datetime.now()
            user_info.update_person = request.user.id
            if telephone:
                user_info.telephone = telephone

            user_info.accounts = accounts
            user_info.gender = gender
            user_info.remarks = remarks
            if request.user.role != 3:
                logger.warning('代理商企图修改截止时间,修改人id为:%d' % request.user.id)
                # 代理商无法修改有效期
                mem.end_time = end_time
            mem.update_person = request.user.id
            mem.update_time = datetime.now()

            user_info.save()
            mem.save()

        except Exception as e:
            logger.error(e)
            pass

        try:
            if is_update_password:
                user.password = make_password(password)

            # 修改时间和修改人
            user.update_person = request.user.id
            user.update_time = datetime.now()
            user.role = role

            if name:
                user.name = name
            if email:
                user.email = email
            user.save()

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RET.DBERR, 'message': '数据库错误'})

        return JsonResponse({'code': RET.OK, 'message': '成功'})


# /users/register
class RegisterView(LoginRequireView):
    def post(self, request):
        """
        创建用户接口
        """
        json_dict = get_json_data(request)
        if json_dict is None:
            return JsonResponse({"code": RET.PARAMERR, "message": "请使用json格式数据"})

        user_name = json_dict.get('adminName')
        name = json_dict.get('name')
        password = json_dict.get('password')
        email = json_dict.get('email')
        role = json_dict.get('adminRole')
        gender = json_dict.get('sex')
        remarks = json_dict.get('remarks')
        telephone = json_dict.get('phone')
        accounts = json_dict.get('accounts')
        end_time = json_dict.get('end_time')

        try:
            # 转换为时间格式
            end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        except Exception:
            end_time = datetime.now() + timedelta(hours=settings.ACCOUNTS_VALID_HOURS)

        # 可以缺省的参数,给定默认值
        email = 'xxxxx@hellocial.com' if email is None else email
        remarks = "" if remarks is None else remarks
        telephone = '13011111111' if telephone is None else telephone
        gender = 0 if gender is None else gender
        role = 6 if role is None else role
        accounts = 0 if accounts is None else accounts

        name = name if name else user_name

        # 代理商只能开临时账户,临时账户有效期为3个小时
        if request.user.role == 3:
            role = 6
            accounts = 0
            end_time = datetime.now() + timedelta(hours=3)

        # 广告主只能开广告操作员,广告操作员账户有效期要小于等于开户的广告主的有效时间
        if request.user.role == 4:
            role = 5
            accounts = 0
            try:
                slef_end_time = MemberShip.objects.get(slave=request.user).end_time
                # 如果广告操作员有效时间超出广告主有效时间,将其置为广告主的有效操作时间
                if slef_end_time < end_time:
                    end_time = slef_end_time
            except Exception as e:
                logger.error(e)
                return JsonResponse({'code': RET.DBERR, 'message': '数据库错误'})

        # 广告主默认开户数为5
        if role == 4:
            accounts = settings.ACCOUNTS_CREATE_COUNT if accounts is None else accounts

        # 校验参数
        if not all([user_name, password]):
            return JsonResponse({"code": RET.PARAMERR, "message": "参数不完整"})

        # 如果密码传过来没有做md5加密
        if len(password) != 32:
            logger.info('密码没有md5加密传输')
            encoder = hashlib.md5()
            encoder.update(password.encode(encoding='utf-8'))
            password = password.hexdigest().lower()

        if len(user_name) < settings.USERNAME_MIN_LENGTH:
            return JsonResponse({'code': RET.PARAMERR, 'message': '用户名长度不足'})

        # 改大写
        user_name = user_name.upper()

        try:
            gender = int(gender)
            role = int(role)
            accounts = int(accounts)
        except Exception as e:
            logger.debug(e)
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数格式错误'})

        if role > 6 or role < 1:
            logger.warning('用户的role参数错误')
            return JsonResponse({'code': RET.PARAMERR, 'message': '角色参数为[1,6]的数字'})

        f_id = json_dict.get('fornum_id')

        if f_id is None:
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数不足'})

        if not isinstance(f_id, Iterable) or isinstance(f_id, str):
            f_id = [f_id]

        try:
            f_id = list(filter(filter_null, f_id))
        except Exception:
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数错误'})

        if gender not in [0, 1]:
            return JsonResponse({'code': RET.PARAMERR, 'message': '性别必须为0和1'})

        # 检测用户名是否已经存在
        try:
            user = User.objects.get(username=user_name)
        except User.DoesNotExist:
            user = None
        if user is not None:
            logger.debug('用户名重复')
            return JsonResponse({"code": RET.USERERR, "message": "用户名已存在"})

        is_super_user = False
        # 检查用户可以开户个数
        try:
            curr_user = UserInfo.objects.get(user=request.user)
            curr_accounts = curr_user.accounts
            has_accounts = curr_user.has_accounts
        except Exception:
            curr_accounts = -1
            has_accounts = -1
            is_super_user = True

        if curr_accounts == 0:
            logger.warning('越权创建账户')
            return JsonResponse({'code': RET.USERERR, 'message': '您没有权限创建账户'})

        # 检查已开户数是否满足要求
        if curr_accounts > 0:
            # 当前用户创建的在有效期内的账户数量
            # has_accounts = MemberShip.objects.filter(master=request.user, end_time__gt=datetime.now()).count()
            # 当前用户的所有账户数量
            has_accounts = MemberShip.objects.filter(master=request.user).all().count()

            if has_accounts >= curr_accounts:
                logger.debug('超过创建用户的限制')
                # 超出了允许拥有的账户数量
                return JsonResponse({'code': RET.USERERR, 'message': '用户可开户账户数已到上限'})

        try:

            # 开启事务,防止创建表失败还添加了新用户
            with transaction.atomic():
                # 保存用户主表
                user = User.objects.create_user(
                    user_name,
                    email,
                    password,
                    role=role,
                    founder=request.user.id,
                    name=name,
                    update_person=request.user.id
                )
        except Exception as e:
            logger.info(e)
            return JsonResponse({'code': RET.PARAMERR, 'message': '用户名已存在'})

        try:
            with transaction.atomic():
                # 保存用户信息表
                user_info = UserInfo.objects.create(
                    user=user,
                    remarks=remarks,
                    telephone=str(telephone),
                    gender=gender,
                    accounts=accounts,
                    founder=request.user.id,
                    update_person=request.user.id
                )

                # 保存用户关系表
                mem_ship = MemberShip.objects.create(
                    master=request.user,
                    slave=user,
                    end_time=end_time,
                    founder=request.user.id,
                    update_person=request.user.id,
                )

                # 如果不是创建工作人员,记录用户指定的论坛

                fornums = Fornum.objects.filter(id__in=f_id).all()
                if len(fornums) != len(f_id):
                    raise Exception('程序id参数有误')

                if request.user.role > 2:
                    # 操作者不是工作人员,校验其自身的论坛
                    user_ps = UserFornumRelation.objects.filter(user=request.user).all()
                    can_f_ids = [r.fornum.id for r in user_ps]
                    for i in f_id:
                        if int(i) not in can_f_ids:
                            raise Exception('程序id参数有误')

                for fornum in fornums:
                    user_p = UserFornumRelation.objects.create(
                        user=user,
                        fornum=fornum,
                        founder=request.user.id,
                        update_person=request.user.id,
                        update_time=datetime.now()
                    )
                    user_p.save()

                user.save()
                user_info.save()
                mem_ship.save()

                if not is_super_user:
                    # 更新当前用户拥有的账户数
                    curr_user.has_accounts = has_accounts + 1
                    curr_user.save()

        except Exception as e:
            logger.error('创建用户失败：%s' % e)
            return JsonResponse({'code': RET.DBERR, 'message': '数据库错误'})

        return JsonResponse({'code': RET.OK, 'message': '添加成功！'})


# /users/pwd
class PasswordView(OnlyLoginRequireView):
    def post(self, request):
        u_id = request.GET.get('id')
        json_dict = get_json_data(request)
        pwd = json_dict.get('password')
        if not pwd:
            return JsonResponse({'code': RET.PARAMERR, 'message': '参数错误'})

        if len(pwd) != 32:
            return JsonResponse({'code': RET.PARAMERR, 'message': '密码需要32位md5加密传输'})

        pwd = pwd.lower()

        if u_id:
            if request.user.role not in [1, 2]:
                logger.warning('没有权限的用户在修改别人的密码,修改人id:%d ' % request.user.id)
                return JsonResponse({'code': RET.USERERR, 'message': '用户权限不足'})

            try:
                user = User.objects.get(id=u_id)
            except Exception as e:
                logger.debug(e)
                return JsonResponse({'code': RET.PARAMERR, 'message': '用户id错误'})

        else:
            user = request.user

        user.password = make_password(pwd)

        user.save()

        return JsonResponse({'code': RET.OK, 'message': '成功'})


# /users/login
class LoginView(View):
    """登录视图"""

    def post(self, request):

        json_dict = get_json_data(request)
        if json_dict is None:
            return JsonResponse({"code": RET.PARAMERR, "message": "请使用json格式数据"})

        # 用户名
        username = json_dict.get("user_name")
        # 密码  要md5加密不然不匹配
        password = json_dict.get("password")
        # 验证码
        checkcode = json_dict.get("checkcode")
        # 验证码的uuid
        uuid = json_dict.get('uuid')

        # 校验完整性
        if not all([username, password, uuid, checkcode]):
            return JsonResponse({"code": RET.PARAMERR, "message": "参数不完整"})

        # 如果密码传过来没有做md5加密
        if len(password) != 32:
            logger.info('密码传输没有进行md5加密')
            encoder = hashlib.md5()
            encoder.update(password.encode(encoding='utf-8'))
            password = encoder.hexdigest().lower()

        if len(username) < 4:
            return JsonResponse({"code": RET.USERERR, "message": "密码或账户名错误"})

        # 获取redis链接,校验验证码
        redis_conn = get_redis_connection('default')
        imageCode_server = redis_conn.get('ImageCode:' + uuid)

        try:
            imageCode_server = imageCode_server.decode()
        except Exception:
            logger.debug("验证码过期")
            return JsonResponse({"code": RET.DBERR, "message": "验证码已过期"})

        if not imageCode_server:
            return JsonResponse({"code": RET.DBERR, "message": "验证码已过期"})

        if imageCode_server.lower() != checkcode.lower():
            logger.debug('验证码错误')
            return JsonResponse({"code": RET.USERERR, "message": "验证码输入错误"})

        # 检查用户名密码是否错误
        user = authenticate(username=username.upper(), password=password, is_delete=False)

        if user is None or user.is_delete:
            return JsonResponse({"code": RET.USERERR, "message": "密码或账户名错误"})

        if not user.is_active:
            # 判断账户是否过期
            return JsonResponse({'code': RET.USERERR, "message": "账户已停用"})

        try:
            mem = MemberShip.objects.get(slave=user)
            if mem.end_time < datetime.now():
                # 过期了更改激活标记
                user.is_active = False
                user.save()
                return JsonResponse({'code': RET.USERERR, "message": "账户已停用"})
        except Exception:
            logger.warning('用户{}缺乏隶属信息'.format(request.user.username))
            pass

        if user.role > 3:
            return JsonResponse({'code': RET.USERERR, 'message': '对不起,您没有权限登陆后台管理界面'})

        try:
            ul = UserLogs.objects.create(
                user=user,
                softwareType=-1,
                load_ip=getIPFromDJangoRequest(request)
            )
            ul.save()
        except Exception as e:
            logger.warn(e)

        # 记录登录状态
        login(request, user)

        return JsonResponse({
            "code": RET.OK,
            "message": "登陆成功"
        })


# /users/app/login2
class AppLogin2View(View):
    """app登录接口"""

    def post(self, request):
        """
        参数:
                mac_address　　MAC地址参数
                user_name    用户名
                password    密　码
                fornum_code    论坛编号
        """

        json_dict = get_json_data(request)

        if json_dict is None:
            return JsonResponse({"code": RET.PARAMERR, "message": "请使用json格式数据"})

        # 用户名
        username = json_dict.get("user_name")
        # 密码  要md5加密不然不匹配
        password = json_dict.get("password")
        # mac地址
        mac_add = json_dict.get("mac_address")
        # 论坛编号
        fornum_code = json_dict.get('fornum_code')

        # 校验完整性
        if not all([username, password, mac_add, fornum_code]):
            logger.debug('登陆参数不完整')
            return JsonResponse({"code": RET.PARAMERR, "message": "参数不完整"})

        if len(password) != 32:
            return JsonResponse({'code': RET.PARAMERR, 'message': '密码或账户名错误'})

        if len(username) < 4:
            return JsonResponse({"code": RET.USERERR, "message": "密码或账户名错误"})

        # 检查用户名密码是否错误
        user = authenticate(username=username.upper(), password=password)

        if user is None or user.is_delete:
            return JsonResponse({"code": RET.USERERR, "message": "密码或账户名错误"})

        if not user.is_active:
            # 判断账户是否过期
            return JsonResponse({'code': RET.USERERR, "message": "账户已停用"})

        # 校验程序对应论坛用户是否有使用权限
        try:
            fornum = Fornum.objects.get(title=fornum_code)
        except Exception as e:
            logger.debug('论坛编号错误')
            return JsonResponse({'code': RET.PARAMERR, 'message': '论坛代号错误'})

        uf_ids = [uf.fornum.id for uf in UserFornumRelation.objects.filter(user=user).all()]

        if fornum.id not in uf_ids:
            logger.debug('账户没有使用该软件的权限')
            return JsonResponse({'code': RET.USERERR, 'message': '账户没有使用该软件的权限'})

        try:
            mem = MemberShip.objects.get(slave=user)

            if user.role == 6:
                if user.last_login is None:
                    mem.end_time = datetime.now() + timedelta(hours=3)
                    mem.save()

            if mem.end_time < datetime.now():
                # 过期了切换账号状态
                user.is_active = False
                user.save()
                return JsonResponse({'code': RET.USERERR, "message": "账户已停用"})
        except Exception as e:
            logger.warning('%s没有隶属关系记录' % user.username)
            pass

        # 校验用户使用的机器部分
        ip_add = getIPFromDJangoRequest(request)

        machines = Machine.objects.filter(user=user, mac_add=mac_add).all()
        # 不是新的机器要更新ip,是新的用户要校验是否满足机器个数的限制,记录机器的mac地址和ip
        if machines.count():
            # 不是0,是已经登陆过的机器,记录IP地址,每个机器,对应单独用户只记录一次
            try:
                machine = machines.first()
                if not machine.is_active:
                    return JsonResponse({'code': RET.USERERR, 'message': '该机器已被禁用'})
                machine.last_ip_add = ip_add
                machine.last_login = datetime.now()
                machine.save()
            except Exception as e:
                logger.error(e)
                return JsonResponse({'code': RET.DBERR, 'message': '数据库错误'})
        else:
            # 是0,说明是新机器,需要校验账户是否有足够的权限进行登陆操作
            if user.role in [3, 5, 6]:
                # 代理商和临时账号,广告操作员
                if Machine.objects.filter(user=user).all().count():
                    return JsonResponse({'code': RET.USERERR, 'message': '使用中设备已达上限'})
            elif user.role != 1:
                # 广告主和后台操作员
                used_machine_count = Machine.objects.filter(user=user).all().count()
                try:
                    user_info = UserInfo.objects.get(user=user)
                    if user_info.accounts <= used_machine_count:
                        return JsonResponse({'code': RET.USERERR, 'message': '可用设备已达上限'})
                except Exception as e:
                    logger.error("用户%s,遇到%s" % (user.username, e))
                    return JsonResponse({'code': RET.DBERR, 'message': '数据库错误', })

            # 走到这里说明账号可以使用新机器,向machine表中插入一条数据
            try:
                machine = Machine.objects.create(
                    user=user,
                    mac_add=mac_add,
                    last_ip_add=ip_add,
                    last_login=datetime.now(),
                    is_active=True
                )
                machine.save()
            except Exception as e:
                logger.error(e)
                return JsonResponse({'code': RET.DBERR, 'message': '数据库出了点问题'})

        try:
            ul = UserLogs.objects.create(
                user=user,
                softwareType=fornum.id,
                load_ip=getIPFromDJangoRequest(request),
                mac_add=mac_add
            )
            ul.save()
        except Exception as e:
            logger.warn(e)

        # 记录登录状态
        login(request, user)

        return JsonResponse({
            "code": RET.OK,
            "message": "登陆成功"
        })


# /users/app/login
class AppLogin1View(View):
    """app登录接口
    该接口已经停用
    """

    def post(self, request):
        json_dict = get_json_data(request)
        if json_dict is None:
            return JsonResponse({"code": RET.PARAMERR, "message": "请使用json格式数据"})

        # TODO:停用该接口
        return JsonResponse({'code': RET.USERERR, 'message': '请使用新版程序'})


# /users/checkcode
class CheckCodeView(View):
    """图片验证码"""

    def get(self, request):
        uuid = request.GET.get('uuid')
        last_uuid = request.GET.get('last_uuid')
        if not uuid:
            # 参数不全,返回错误信息
            return JsonResponse({'errorcode': RET.PARAMERR, 'errormsg': "参数错误"})
        # text:验证码的文本信息   image:验证码的图片一张
        image, text = Captcha.gene_code()

        redis_conn = get_redis_connection('default')

        try:
            # 将图片的UUID存储到redis数据库中,过期时间设置为300秒
            redis_conn.set('ImageCode:' + uuid, text, settings.IMAGE_CODE_REDIS_EXPIRES)
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RET.DBERR, 'message': "数据库错误"})

        if last_uuid is not None:
            # 删除之前的图片验证码的UUID
            redis_conn.delete('ImageCode:' + last_uuid)

        # 设置响应的内容类型为图片
        return HttpResponse(image, content_type='image/jpeg')


# /users/loginout
class LoginOutView(OnlyLoginRequireView):
    """登出"""

    def get(self, request):
        logout(request)
        return JsonResponse({
            "code": RET.OK,
            "message": "退出登录成功"
        })


# /users/user_fornum
class UserFornumView(LoginRequireView):
    """用户可用论坛管理视图"""

    def get(self, request):
        """
        如果不传id就默认返回当前登陆的人的论坛信息,传了id就返回该id对应的人的论坛关系信息
        :param request:
        :return:
        """
        u_id = request.GET.get('id')
        if u_id is None:
            user = request.user
        else:
            try:
                user = User.objects.get(id=u_id)
            except Exception as e:
                logger.debug(e)
                return JsonResponse({'code': RET.PARAMERR, 'message': '参数错误'})

        user_f_rels = UserFornumRelation.objects.filter(user=user).all()

        data = []
        for user_f_rel in user_f_rels:
            d = {
                'fornum_name': user_f_rel.fornum.fornum_name,
                'fornum_title': user_f_rel.fornum.title,
                'fornum_id': user_f_rel.fornum.id,
            }
            data.append(d)
        return JsonResponse({'code': RET.OK, 'message': 'OK', 'data': data})


# /search
class SearchResultView(OnlyLoginRequireView):
    def get(self, request):
        q = request.GET.get('q')
        page = request.GET.get('page')
        if request.user.role <= 2:
            users = User.objects.filter(models.Q(name__icontains=q) | models.Q(username__icontains=q)).all()
        else:
            mems = MemberShip.objects.filter(master=request.user).all()
            mems = mems.filter(models.Q(slave__name__icontains=q) | models.Q(slave__username__icontains=q))
            users = [mem.slave for mem in mems]

        data = []

        try:
            page = int(page)
        except TypeError:
            page = 1

        # 每页10条数据
        paginator = Paginator(users, settings.PER_PAGE_COUNTS)

        if (page > paginator.num_pages) or (page < 0):
            page = 1

        users = paginator.page(page)

        for user in users:

            # 论坛信息展示
            ufrs = UserFornumRelation.objects.filter(user=user).all()
            u_fornums = []
            for ufr in ufrs:
                f = {
                    'fornum_name': ufr.fornum.fornum_name,
                    'fornum_id': ufr.fornum.id,
                    'fornum_code': ufr.fornum.title
                }
                u_fornums.append(f)

            try:
                mem = MemberShip.objects.get(slave=user)
                remain_days = (mem.end_time - datetime.now()).days
                remain_days = remain_days if remain_days >= 0 else -1
                end_date = mem.end_time.strftime("%Y年%m月%d日 %H:%M")
                parent_name = mem.master.name
                parent_id = mem.master.id
                parent_role = mem.master.role
                remarks = user.userinfo_set.first().remarks
            except MemberShip.DoesNotExist:
                logger.info("%s没有隶属关系信息" % user.username)
                remain_days = -1
                end_date = -1
                parent_id = -1
                parent_name = ''
                parent_role = -1
                remarks = ""
            try:
                d = {
                    'parent_name': parent_name,
                    'parent_role': parent_role,
                    'parent_id': parent_id,
                    'id': user.id,
                    'username': user.username,
                    'name': user.name,
                    'email': user.email,
                    'role': user.role,
                    'remain_days': remain_days,
                    'remarks': remarks,
                    'join_date': user.date_joined.strftime("%Y年%m月%d日 %H:%M"),
                    'end_date': end_date,
                    'is_in_use': user.is_active,
                    'fornums': u_fornums
                }
            except Exception as e:
                logger.error(e)
                continue
            data.append(d)

        return JsonResponse({'code': RET.OK, 'message': '成功', 'data': data, 'pages': paginator.num_pages,
                             'data_length': paginator.count})



