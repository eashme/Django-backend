LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        }, # 针对 DEBUG = True 的情况
    },
    'formatters': {
        'standard': {
            'format': '%(levelname)s %(asctime)s %(pathname)s %(lineno)d: %(message)s'
        },
        # INFO 2016-09-03 16:25:20,067 /home/ubuntu/mysite/views.py 29: some info...
    },
    'handlers': {
        'debug_file_handler': {
             'level': 'DEBUG',
             'class': 'logging.handlers.TimedRotatingFileHandler',
             # 'filename': '/root/Hellocial/logs/django_logs/debug.logs',
            'filename': './logs/django_logs/debug.logs',
            'formatter':'standard'
        }, # 用于文件输出
        'warning_file_handler': {
             'level': 'WARNING',
             'class': 'logging.handlers.TimedRotatingFileHandler',
             # 'filename': '/root/Hellocial/logs/django_logs/warning.logs',
            'filename': './logs/django_logs/warning.logs',
            'formatter':'standard'
        }, # 用于文件输出

    },
    'loggers': {
        'django': {
            'handlers' :['debug_file_handler'],
            'level':'DEBUG',
            'propagate': True # 是否继承父类的log信息
        }, # handlers 来自于上面的 handlers 定义的内容
        'django.request': {
            'handlers': ['warning_file_handler'],
            'level': 'WARNING',
            'propagate': True,
        },
    }
}