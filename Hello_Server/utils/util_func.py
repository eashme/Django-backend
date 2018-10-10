import json


def filter_null(i):
    try:
        int(i)
        return True
    except Exception:
        return False


def get_json_data(request):
    try:
        json_dict = json.loads(request.body.decode())
    except Exception:
        json_dict = None

    return json_dict


def getIPFromDJangoRequest(request):
    """获取ip地址"""
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        return request.META['HTTP_X_FORWARDED_FOR']
    else:
        return request.META['REMOTE_ADDR']


def func(*args, **kwargs): pass
