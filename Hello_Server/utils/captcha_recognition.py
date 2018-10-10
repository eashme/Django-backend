import io,requests,gc
from PIL import Image
from urllib.request import urlopen
from django.conf import settings
from utils.response_code import RET


class CaptchaRecognition(object):
    def get_image_obj(self, url):
        try:
            image_bytes = urlopen(url).read()
            # internal data file
            data_stream = io.BytesIO(image_bytes)
            im = Image.open(data_stream)

        except Exception:
            return '获取图片失败'
        return im

    def color_diff(self, a_rgb, c_rgb):
        """比较两种颜色的rgb值返回两种颜色之间的相似度"""
        return (255 - abs(a_rgb[0] - c_rgb[0]) * 0.297 - abs(a_rgb[1] - c_rgb[1]) * 0.593 - abs(
            a_rgb[2] - c_rgb[2]) * 0.11) / 255

    def find_color_area(self, im, window_size=2, weight=0.85, f_rgb=(255, 255, 255), area_count=6):
        """
        深度搜索找色块,根据白色色块辐射出需要保留的颜色区域,并返回
        :param im:  PIL的图片对象
        :param window_size:  窗口大小, 如果为1则为3*3的窗口,如果为2则为 4*4的窗口大小,如果为3则为5*5的窗口大小,以此类推
        :param weight:      相似度阈值,如果相似度大于该值则说明属于该色块
        :param f_rgb:       用于比较的颜色RGB值
        :param area_count:  保留的色块个数
        :return:   返回所有大色块的坐标
        """

        # 窗口偏移量
        offsets = [(i, j) for i in range(-window_size, window_size) for j in range(-window_size, window_size)]

        # 白色区域集合
        white_areas = {}
        # 图像的size
        width, height = im.size
        # 图像的所有坐标穷举
        pos_list = [(x, y) for x in range(width) for y in range(height)]

        # 已经被加入到白色区域字典要跳过的点坐标
        skip_list = set()

        # 遍历所有坐标点
        for pos in pos_list:

            # 如果需要跳过就跳过了
            if pos in skip_list:
                continue

            # 查找列表
            find_list = list()

            find_list.append(pos)

            i = 0

            while True:
                # 当所有点找完之后跳出循环

                try:
                    # 当前色块要找的点
                    l_pos = find_list[i]
                except Exception:
                    break

                i += 1

                # 拿到颜色RGB值
                c_color = im.getpixel(l_pos)

                # 将当前点的RGB值和白色做比较,相似度高于阈值的在其周围找白色点
                if self.color_diff(f_rgb, c_color) > weight:
                    for offset in offsets:
                        # 偏移后的坐标
                        offset_pos = (l_pos[0] + offset[0], l_pos[1] + offset[1])
                        try:
                            o_color = im.getpixel(offset_pos)
                        except IndexError:
                            # 获取失败说明是边界点,跳过
                            continue

                        # 周边的点也与白色计算相似度
                        if self.color_diff(f_rgb, o_color) > weight:
                            try:
                                # 大于阈值的纪录坐标点
                                white_areas[pos].add(offset_pos)
                                # 记录过坐标点的直接加入跳过列表,一点属于多个白色色块
                                skip_list.add(offset_pos)
                                # 将其加入查找队列
                                if offset_pos not in find_list:
                                    find_list.append(offset_pos)

                            except KeyError:
                                white_areas[pos] = set()

        # 重新组合
        white_areas = list(zip(white_areas.keys(), white_areas.values()))

        print("There is {} areas which is white".format(len(white_areas)))

        if len(white_areas) < 80:
            return None

        white_areas.sort(key=lambda x: len(x[:][1]), reverse=True)

        # 要保留的颜色区域和颜色
        save_area = set()
        offsets = [(i, j) for i in range(-2, 2) for j in range(-2, 2)]

        # 将色块范围以外的区域置为白色
        for pos, pos_set in white_areas[:area_count]:
            for pos in pos_set:
                # 由每个点进行辐射一个窗口大小的范围,辐射到的像素点保留颜色,其余像素点置为白色
                save_area.add((pos, im.getpixel(pos)))
                for offset in offsets:
                    offset_pos = (pos[0] + offset[0], pos[1] + offset[1])
                    try:
                        save_area.add((offset_pos, im.getpixel(offset_pos)))
                    except IndexError:
                        continue

        return save_area

    def binary_image(self, im, percent=0.7):
        """
        :param im: PIL的图片对象
        :param weight: 二值化阈值
        :return:
        """
        w, h = im.size

        like_white = []
        # 遍历图像的每个坐标点,获取RGB值
        for x in range(w):
            for y in range(h):
                pos = (x, y)
                c_color = im.getpixel(pos)

                like_white.append((pos, self.color_diff(c_color, (255, 255, 255))))

        like_white.sort(key=lambda x: x[1], reverse=True)

        for pos, likelihood in like_white[:int(len(like_white) * percent)]:
            # 二值化
            im.putpixel(pos, (255, 255, 255))

    def remove_other_color(self, im, dis=35):
        """删除不是灰白黑色的颜色"""
        width, height = im.size
        pos_list = [(x, y) for x in range(width) for y in range(height)]

        for pos in pos_list:
            c_color = im.getpixel(pos)
            distance = abs(c_color[1] - c_color[0]) + abs(c_color[1] - c_color[2]) + abs(c_color[0] - c_color[2])
            if distance > dis:
                # 不是灰白黑色色系
                im.putpixel(pos, (255, 255, 255))

    def save_image(self, im, save_pos, window_size):
        """保存图片辐射的像素点"""
        width, height = im.size
        offsets = [(i, j) for i in range(-window_size, window_size) for j in range(-window_size, window_size)]

        save_list = []
        for pos in save_pos:
            for offset in offsets:
                offset_pos = (pos[0] + offset[0], pos[1] + offset[1])
                try:
                    o_color = im.getpixel(offset_pos)
                except IndexError:
                    continue
                save_list.append([offset_pos, o_color])

        new_im = Image.new('RGB', im.size, color=(255, 255, 255))
        # 内存中删除原图
        del im
        gc.collect()

        for pos, color in save_list:
            new_im.putpixel(pos, color)

        return new_im


class DoubanCaptchaRecognition(CaptchaRecognition):
    def process_english(self, im):
        """
        处理英文验证码的函数
        :param im:
        :return:
        """
        areas = self.find_color_area(im, 2, 0.95, (0, 0, 0), 10)

        if areas is None:
            raise Exception('黑色太多识别不了')

        im = Image.new(mode='RGB', size=(400, 60), color=(255, 255, 255))

        for pos, color in list(areas):
            im.putpixel(pos, color)

        return im

    def process_chinese(self, im):
        """
        处理中文验证码的函数
        :param im:
        :return:
        """
        save_area = self.find_color_area(im, 3, 0.95, (255, 255, 255), 10)

        if save_area is None:
            raise Exception('白色区域过多,识别不了')

        im = Image.new(mode='RGB', size=(400, 60), color=(255, 255, 255))

        for pos, color in list(save_area):
            im.putpixel(pos, color)

        pos_list = self.get_words(im, weight=0.85, window_size=3)

        im = self.save_image(im, save_pos=pos_list, window_size=3)

        self.remove_other_color(im)

        self.binary_image(im, 0.94)

        return im

    def get_words(self, im, weight, window_size):
        width, height = im.size
        pos_list = [(x, y) for x in range(width) for y in range(height)]

        # 窗口偏移量
        offsets = [(i, j) for i in range(-window_size, window_size) for j in range(-window_size, window_size)]

        words = []

        for pos in pos_list:
            c_color = im.getpixel(pos)
            # 如果该颜色和黑色相近,则在其附近找白色
            if self.color_diff((0, 0, 0), c_color) > weight:

                score = 0

                for offset in offsets:
                    offset_pos = (pos[0] + offset[0], pos[1] + offset[1])
                    try:
                        o_color = im.getpixel(offset_pos)
                    except IndexError:
                        continue

                    if self.color_diff(o_color, (255, 255, 255)) > weight:
                        # 在黑色点的窗口中找到了白色
                        score += 1

                if score > round((len(offsets) / 4)):
                    # 所有窗口中有四分之一的窗口是白色则记录下来
                    words.append(pos)
        return words


class RuoKuaiCaptcha(object):
    RuoKuai_url = "http://api.ruokuai.com/"

    def __init__(self, username, password, soft_id=None, soft_key=None):
        """
        :param username:  当前使用打码服务的账号
        :param password:  当前使用打码服务的账户密码(需要MD5加密)
        :param soft_id:   开发者账号的soft_id
        :param soft_key:  开发者账号的soft_key
        """
        self.username = username
        self.password = password
        self.soft_id = soft_id if soft_id else  settings.RUOKUAI_SOFT_ID
        self.soft_key = soft_key if soft_key else settings.RUOKUAI_SOFT_KEY
        self.base_params = {
            'username': self.username,
            'password': self.password,
            'softid': self.soft_id,
            'softkey': self.soft_key,
        }
        self.headers = {
            'Connection': 'Keep-Alive',
            'Expect': '100-continue',
            'User-Agent': 'ben',
        }

    def _create(self, im, im_type, timeout=60):
        params = {
            'typeid': im_type,
            'timeout': timeout,
        }
        params.update(self.base_params)
        files = {'image': ('a.jpg', im.tobytes('jpeg', 'RGB'))}
        r = requests.post(self.RuoKuai_url + 'create.json', data=params, files=files, headers=self.headers)
        return r.json()

    def get_error_info(self, im_id):
        """
        im_id:报错图片的ID
        """
        params = {
            'id': im_id,
        }
        params.update(self.base_params)
        r = requests.post(self.RuoKuai_url + 'reporterror.json', data=params, headers=self.headers)
        return r.json()

    def get_string(self,im,im_type):
        try:
            json_dict = self._create(im,im_type)
        except Exception as e:
            print(e)
            return {'code':RET.SERVERERR,'message':'网络错误'}
        # {"Result":"答题结果","Id":"题目Id(报错使用)"}
        # {"Error":"错误提示信息","Error_Code":"错误代码（详情见错误代码表）","Request":""}
        result = json_dict.get('Result')
        if not result:
            err_msg = json_dict.get('Error')
            return {
                'code':RET.THIRDERR,
                'message': err_msg if err_msg else '若快打码平台解析失败'
            }

        return {'code':RET.OK,'message':'成功','result':result}
