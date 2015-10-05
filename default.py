"""
Bu dosya livechat uygulamasinin temek ayarlarini icermektedir.

Production veya development gibi ozel ortamlar icin ihtiyac duyacaginiz
ayarlari bu dosya ile ayni dizinde bulunan, asagidaki siniflardan turettiginiz
siniflar icinde tanimlayiniz. Asagidakiler ortam konfigurasyonlari icin
temel degerleri icermektedir.

Ornegin beta testi icin ortam hazirlarken farkli veritabani konfigurasyonlarina
ihtiyac duyabilirsiniz. Bu ihtiyacinizi buradaki degerleri degistirerek
gidermemeliziniz. Bunun yerine ayni dizin icersinde beta.py isimli bir dosya
olusturun ve beta.py icinde Config() isimli, default.Config'ten miras alan
sinif tanimlayin ve LIVECHAT_ENV ortam degiskenine 'beta' degerini atayin.
Bu beta.py, __init__.py icindeki get() metodundan cagrilacaktir.

"""
from datetime import timedelta


class Config(object):
    """
    Bu sinif dogrudan kullanilmamaktadir, ancak diger siniflar
    tarafindan miras alinir. Genel ayarlari buraya yaziniz.

    """
    NAME = 'default.config'
    SECRET_KEY = 'flj is not apparent'
    HOSTNAME = 'www.flj.com'
    HTTP_PROTOCOL = "https"
    HOSTNAME_WITH_PROTOCOL = 'http://www.flj.com'

    # connectiong parameters for mongodb database
    MONGODB_DATABASENAME = 'flj'
    MONGODB_URI = 'mongodb://user:password@localhost/flj'

    CONTACT_US_EMAIL = 'info@flj.com'

    # MAILGUN'S EMAIL SERVICE SETTINGS
    MAILGUN_API_ENDPOINT = "https://api.mailgun.net/v3/"
    MAILGUN_API_DOMAIN = "mg.flj.com"
    MAILGUN_API_KEY = "key-b362316f54ec9916e8e84af29f0748ab"
    MAILGUN_NEWSLETTER = "updates@mg.flj.com"
    MAILGUN_API_FROM = "FLJ Support <postmaster@mg.flc.com>"

    # LOGGING, REF: PYTHON logging-config-dictschema
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'verbose': {
                'format': '%(asctime)s - %(levelname)s - %(module)s: ' +
                '%(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'colored': {
                '()': 'colorlog.ColoredFormatter',
                'format': '%(log_color)s%(asctime)s - %(levelname)s' +
                ' - %(module)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s %(message)s'
            },
        },
        'handlers': {
            'null': {
                'class': 'logging.NullHandler',
            },
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'colored'
            },
            'file': {
                'class': 'logging.handlers.WatchedFileHandler',
                'filename': '/var/log/flj/api.log',
                'formatter': 'colored',
                'encoding': 'utf-8',
                'delay': True
            },
            'socketFile': {
                'class': 'logging.handlers.WatchedFileHandler',
                'filename': '/var/log/flj/socketServer.log',
                'formatter': 'colored',
                'encoding': 'utf-8',
                'delay': True
            },
            'celeryWorker': {
                'class': 'logging.handlers.WatchedFileHandler',
                'filename': '/var/log/flj/celeryWorker.log',
                'formatter': 'colored',
                'encoding': 'utf-8',
                'delay': True
            }
        },
        'loggers': {
            '': {
                'handlers': ['file', 'console'],
                'propagate': True,
                'level': 'INFO'
            },
            'celeryWorker': {
                'handlers': ['celeryWorker'],
                'level': 'INFO',
                'propagate': False,
            }
        }
    }

    # Sosyal
    # FACEBOOK_APP_ID = '324656944355599'
    # FACEBOOK_APP_SECRET = '5ba6e8aa7d396489dc83074aab916dcb'

    # SHOPIFY_KEY = '025bd5ab212faaa0187b52768f67cb25'
    # SHOPIFY_SECRET = '85f2b73af01c44468a6752fc370f3ae2'

    # GOOGLE_CLIENT_ID = '495259304014-j4hgmjqi8277h49oh4vavcom'
    # GOOGLE_CLIENT_SECRET = 'JkzTQYEk7H2_2miu-UxKJj-u'

    # CELERY
    # RETRY_DELAY = timedelta(minutes=60)
    # CELERY_NAME = 'flj'
    # CELERY_TIMEZONE = 'UTC'
    # CELERY_RESULT_BACKEND = "mongodb://localhost//"
    # CELERY_MONGODB_BACKEND_SETTINGS = {
    #     'database': 'flj',
    #     'taskmeta_collection': 'tasks',
    # }
    # BROKER_URL = 'amqp://localhost/'
    # BROKER_TRANSPORT_OPTIONS = {
    #     'visibility_timeout': 196000,
    #     'fanout_patterns': True
    #     }

    # CELERY_DEFAULT_QUEUE = 'flj'
    # CELERY_DEFAULT_ROUTING_KEY = 'flj'

    # CELERY_DEFAULT_EXCHANGE = 'flj'
    # CELERYD_CONCURRENCY = 2
    # CELERYD_PREFETCH_MULTIPLIER = 2
    # CELERYD_TASK_SOFT_TIME_LIMIT = 60 * 4
    # CELERYD_TASK_TIME_LIMIT = 60 * 5
    # CELERYBEAT_SCHEDULE = {
    #     'daily_stats':{
    #         'task': 'task1',
    #         'schedule': timedelta(minutes=60),
    #         'args': []
    #     },
    #     'widget_looper':{
    #         'task': 'task2',
    #         'schedule': timedelta(minutes=10),
    #         'args': []
    #     },
    #     'status_controller': {
    #         'task': 'task3',
    #         'schedule': timedelta(minutes=15),
    #         'args': []
    #     }

    # }


class Dev(Config):
    """
    Gelistirme ortaminda calisacak uygulamanin ayarlari buradan
    belirlenir. Config'ten gelen direktiflerin uzerine
    yazabilir veya gelistirme ortamina ozel yeni direktifler
    ekleyebilirsiniz.
    """
    DEBUG = True
    NAME = 'default.dev'
    HTTP_PROTOCOL = "http"

    MONGODB_DATABASENAME = 'flj_dev'
    MONGODB_URI = 'mongodb://localhost/flj_dev'

    # MAILGUN'S EMAIL SERVICE SETTINGS
    def __init__(self):
        # http://stackoverflow.com/questions/576169/understanding-python-super-with-init-methods
        # super(self.__class__, self).__init__()
        Config.__init__(self)
        self.LOGGING['loggers']['']['level'] = 'DEBUG'


class Test(Config):
    """
    Test ortaminda calisacak uygulamanin ayarlari buradan belirlenir.
    """

    NAME = 'default.test'
    HOSTNAME_WITH_PROTOCOL = 'http://flj/'

    MONGODB_DATABASENAME = 'flj_test'
    MONGODB_URI = 'mongodb://localhost/flj_testing'

    def __init__(self):
        Config.__init__(self)
        self.LOGGING['loggers']['']['level'] = 'DEBUG'
