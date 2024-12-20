"""
Django settings for oneup_project project.

Generated by 'django-admin startproject' using Django 4.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
from datetime import timedelta
import os
from pathlib import Path
from oscar.defaults import *

# from django.utils.translation import ugettext_lazy as _
from django.utils.translation import gettext_lazy as _
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-01bna4o&e4!jo=e7^mm6)#x*x102g35j6@uefr%_0uyc+pna=x"
# OSCAR_HOMEPAGE = '/accounts/login/'
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG')
SITE_ID = 1
ALLOWED_HOSTS = ["*"]


CORS_ALLOW_CREDENTIALS = True

CORS_ORIGIN_ALLOW_ALL = True

CORS_ALLOW_CREDENTIALS = True


CSRF_TRUSTED_ORIGINS = ["https://adminoneup.stackerbee.com/"]

CORS_REPLACE_HTTPS_REFERER = True

# CSRF_COOKIE_DOMAIN = 'elitetraveltech.in'

CORS_ORIGIN_WHITELIST = (
    "https://adminoneup.stackerbee.com/",
    "adminoneup.stackerbee.com",
    "stackerbee.com",
    "https://oneupbrands.com/"
)


REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}


# Application definition

INSTALLED_APPS = [
    "django_crontab",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.flatpages",
    "mathfilters",
    # django database backup
    "dbbackup",
    "oscar.config.Shop",
    "oscar.apps.analytics.apps.AnalyticsConfig",
    "oscar.apps.checkout.apps.CheckoutConfig",
    # 'oscar.apps.address.apps.AddressConfig',
    "oscar.apps.shipping.apps.ShippingConfig",
    # 'oscar.apps.catalogue.apps.CatalogueConfig',
    "apps.address.apps.AddressConfig",
    #'oscar.apps.catalogue.apps.CatalogueConfig',
    "apps.catalogue.apps.CatalogueConfig",
    "oscar.apps.catalogue.reviews.apps.CatalogueReviewsConfig",
    "oscar.apps.communication.apps.CommunicationConfig",
    # 'oscar.apps.partner.apps.PartnerConfig',
    "apps.partner.apps.PartnerConfig",
    #'oscar.apps.basket.apps.BasketConfig',
    "apps.basket.apps.BasketConfig",
    "oscar.apps.payment.apps.PaymentConfig",
    "oscar.apps.offer.apps.OfferConfig",
    "apps.order.apps.OrderConfig",
    "oscar.apps.customer.apps.CustomerConfig",
    "oscar.apps.search.apps.SearchConfig",
    # 'oscar.apps.voucher.apps.VoucherConfig',
    "apps.voucher.apps.VoucherConfig",
    # 'oscar.apps.wishlists.apps.WishlistsConfig',
    "apps.wishlists.apps.WishlistsConfig",
    #'oscar.apps.dashboard.apps.DashboardConfig',
    #'oscar.apps.wishlists.apps.WishlistsConfig',
    # 'oscar.apps.dashboard.apps.DashboardConfig',
    "apps.dashboard.apps.DashboardConfig",
    "oscar.apps.dashboard.reports.apps.ReportsDashboardConfig",
    "oscar.apps.dashboard.users.apps.UsersDashboardConfig",
    "oscar.apps.dashboard.orders.apps.OrdersDashboardConfig",
    # 'oscar.apps.dashboard.catalogue.apps.CatalogueDashboardConfig',
    "apps.dashboard.catalogue.apps.CatalogueDashboardConfig",
    "oscar.apps.dashboard.offers.apps.OffersDashboardConfig",
    "oscar.apps.dashboard.partners.apps.PartnersDashboardConfig",
    "oscar.apps.dashboard.pages.apps.PagesDashboardConfig",
    "oscar.apps.dashboard.ranges.apps.RangesDashboardConfig",
    "oscar.apps.dashboard.reviews.apps.ReviewsDashboardConfig",
    "oscar.apps.dashboard.vouchers.apps.VouchersDashboardConfig",
    "oscar.apps.dashboard.communications.apps.CommunicationsDashboardConfig",
    "oscar.apps.dashboard.shipping.apps.ShippingDashboardConfig",
    # 3rd-party apps that oscar depends on
    "widget_tweaks",
    "haystack",
    "treebeard",
    "sorl.thumbnail",  # Default thumbnail backend, can be replaced
    "django_tables2",
    "rest_framework",
    "oscarapi",
    "useraccount",
    "homepageapi",
    "bannermanagement",
    "sync_data_erp",
    "DiscountManagement",
    "mycustomapi",
    "MyNewsLetterApi",
    "tinymce",
    "cart_api",
    "role_permission",
    "fshipapi",
    "wallet",
    "credit",
    "apps.dashboard.reports",
    "report",
    "task_runner",
    "log_data.apps.LogDataConfig",
    'debug_toolbar',
]

DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
DBBACKUP_STORAGE_OPTIONS = {"location": "/home/oneup/dbbackup/"}


CRONJOBS = [
    ("0 6 * * *", "oneup_project.cron.dbbackup_func"),
    ("*/1 * * * *", "task_runner.views.Check_order_status"),
    ("*/1 * * * *", "mycustomapi.views.checkout.failed_order_retry"),
    ("*/1 * * * *", "task_runner.views.check_unfreeze"),
    ("*/10 * * * *", "task_runner.views.fetch_payment_status"),
]


SITE_ID = 1


def company_access_fn(user, url_name, url_args, url_kwargs):
    return user.groups.filter(name="company").exists()


def superadmin_access_fn(user, url_name, url_args, url_kwargs):
    return user.is_superuser


def common_company_superuser_access_fn(user, url_name, url_args, url_kwargs):
    return user.is_superuser or user.is_staff


def super_user_func(user, url_name, url_args, url_kwargs):
    return user.is_superuser


OSCAR_DASHBOARD_NAVIGATION = [
    {
        "label": _("Dashboard"),
        "icon": "fas fa-list",
        "url_name": "dashboard:index",
    },
    {
        "label": _("Catalogue"),
        "icon": "fas fa-sitemap",
        "children": [
            {
                "label": _("Products"),
                "url_name": "dashboard:catalogue-product-list",
            },
            {
                "label": _("Product Types"),
                "url_name": "dashboard:catalogue-class-list",
            },
            {
                "label": _("Categories"),
                "url_name": "dashboard:catalogue-category-list",
            },
            # {
            #     "label": _("Low stock alerts"),
            #     "url_name": "dashboard:stock-alert-list",
            # },
            # {
            #     "label": _("Options"),
            #     "url_name": "dashboard:catalogue-option-list",
            # },
        ],
    },
    {
        "label": _("Fulfilment"),
        "icon": "fas fa-shopping-cart",
        "children": [
            {
                "label": _("Orders"),
                "url_name": "full-orders",
                "access_fn": common_company_superuser_access_fn,
            },
            {
                "label": _("Statistics"),
                "url_name": "dashboard:order-stats",
            },
            {
                "label": _("Customers"),
                "url_name": "dashboard:users-index",
            },
            # {
            #     'label': _('Failed Order'),
            #     'url_name': "failed_order",
            #     'access_fn': common_company_superuser_access_fn,
            # },
            # The shipping method dashboard is disabled by default as it might
            # be confusing. Weight-based shipping methods aren't hooked into
            # the shipping repository by default (as it would make
            # customising the repository slightly more difficult).
            # {
            #     'label': _('Shipping charges'),
            #     'url_name': 'dashboard:shipping-method-list',
            # },
        ],
    },
    {
        "label": _("Vouchers & Discount"),
        "icon": "fas fa-bullhorn",
        "children": [
            # {
            #     "label": _("Ranges"),
            #     "url_name": "dashboard:range-list",
            # },
            # {
            #     "label": _("Voucher Type"),
            #     "url_name": "dashboard:offer-list",
            # },
            # {
            #     "label": _("Voucher"),
            #     "url_name": "dashboard:voucher-list",
            # },
            {
                "label": _("Voucher Sets"),
                "url_name": "voucher-sets",
                "access_fn": common_company_superuser_access_fn,
            },
            {
                "label": _("Voucher Requests"),
                "url_name": "voucher-request-user-list",
                "access_fn": common_company_superuser_access_fn,
            },
        ],
    },
    {
        "label": _("Content"),
        "icon": "fas fa-folder",
        "children": [
            # {
            #     "label": _("Pages"),
            #     "url_name": "dashboard:page-list",
            # },
            # {
            #     "label": _("Email templates"),
            #     "url_name": "dashboard:comms-list",
            # },
            # {
            #     "label": _("Reviews"),
            #     "url_name": "dashboard:reviews-list",
            # },
            {
                "label": _(" Main Banners"),
                "url_name": "banner-list",
                "access_fn": common_company_superuser_access_fn,
            },
            {
                "label": _("Category banner"),
                "url_name": "CategoryPromotionList-list",
                "access_fn": common_company_superuser_access_fn,
            },
            {
                "label": _("Manage Brands"),
                "url_name": "manage_brands_list",
                "access_fn": common_company_superuser_access_fn,
            },
        ],
    },
    {
        "label": _("Reports & Integrations"),
        "icon": "fas fa-chart-bar",
        "children": [
            {
                "label": _("Reports"),
                "url_name": "dashboard:reports-index",
            },
            {
                "label": _("Order Integrations"),
                "url_name": "Order-Integrations-list",
                "access_fn": common_company_superuser_access_fn,
            },
            {
                "label": _("Stock Integrations"),
                "url_name": "Stock-Integrations-list",
                "access_fn": common_company_superuser_access_fn,
            },
            {
                "label": _("Product Error Log"),
                "url_name": "error-log",
                "access_fn": common_company_superuser_access_fn,
            },
            {
                "label": _("Product Success Log"),
                "url_name": "success-log",
                "access_fn": common_company_superuser_access_fn,
            },
        ],
    },
    {
        "label": _("Wallet & Credit"),
        "icon": "fas fa-file-import",
        "children": [
            {
                "label": _("Wallet"),
                "url_name": "wallet",
                "access_fn": common_company_superuser_access_fn,
            },
            {
                "label": _("Credit"),
                "url_name": "credit",
                "access_fn": common_company_superuser_access_fn,
            },
            {
                "label": _("Credit Requests"),
                "url_name": "credit-request-user-list",
                "access_fn": common_company_superuser_access_fn,
            },
        ],
    },
    {
        "label": _("User"),
        "icon": "fas fa-user",
        "children": [
            {
                "label": _("Client Requested"),
                "url_name": "ClientRequestList",
                "access_fn": common_company_superuser_access_fn,
            },
            {
                "label": _("Client User"),
                "url_name": "client-list",
                "access_fn": common_company_superuser_access_fn,
            },
            {
                "label": _("Admin User"),
                "url_name": "admin-list",
                "access_fn": super_user_func,
            },
            {
                "label": _("Get Help"),
                "url_name": "get-help-list",
                "access_fn": common_company_superuser_access_fn,
            },
             {
                'label': _("Add Role Type"),
                'url_name': 'add-role',
                'access_fn': common_company_superuser_access_fn,
            },
            # {
            #     'label': _('PromotionalSchemes'),
            #     #'url_name': 'PromotionSchemes',
            #     #'access_fn': lambda user, url_name, url_args, url_kwargs: user.is_staff,
            # },
        ],
    },
    # {
    #     'label': _('ClientList'),
    #     'url_name': 'client-list',
    #     'access_fn': superadmin_access_fn,
    #     },
    #        {
    #     'label': _('Banner management'),
    #     'url_name': 'banner-list',
    #     'access_fn': superadmin_access_fn,
    #     },
    # {
    #     'label': _('Tax'),
    #     "icon": "fas fa-solid fa-money-check-dollar",
    #     'children': [
    #         {
    #             'label': _('GST Code'),
    #             'url_name': 'gst-group-list',
    #             'access_fn': common_company_superuser_access_fn
    #         },
    #         {
    #             'label': _('GST Setup'),
    #             'url_name': 'gst-setup-list',
    #             'access_fn': common_company_superuser_access_fn,
    #         },
    #     ]
    # },
    {
        "label": _("Import"),
        "icon": "fas fa-file-import",
        "url_name": "upload",
        "access_fn": common_company_superuser_access_fn,
    },
    {
        "label": _("Newsletter Management"),
        "icon": "fas fa-solid fa-envelope",
        "children": [
            {
                "label": _("Subscriber List"),
                "url_name": "subscriber-list",
                "access_fn": common_company_superuser_access_fn,
            },
            {
                "label": _("Manage NewsLetter Template"),
                "url_name": "Manage-NewsLetter-Template",
                "access_fn": common_company_superuser_access_fn,
            },
            {
                "label": _("Send NewsLetter"),
                "url_name": "send-newsletter",
                "access_fn": common_company_superuser_access_fn,
            },
            {
                "label": _("Contact List"),
                "url_name": "contact-list",
                "access_fn": common_company_superuser_access_fn,
            },
        ],
    },
    {
        "label": _("Role"),
        "icon": "fas fa-list",
        'access_fn': common_company_superuser_access_fn,
        'children': [
            # {
            #     'label': _('Add URL'),
            #     'url_name': "add-url",
            #     'access_fn': common_company_superuser_access_fn,
            # },
           
            # {
            #     'label': _('Assign User Role'),
            #     'url_name': 'assign-user',
            #     'access_fn': common_company_superuser_access_fn,
            # },
        ],
    },
]


OSCAR_DASHBOARD_DEFAULT_ACCESS_FUNCTION = "oscar.apps.dashboard.nav.default_access_fn"


OSCAR_ORDER_STATUS_PIPELINE = {
    "Created": [
        "Send To erp",
        "Shipped",
        "Partially Shipped",
        "Delivered",
        "Partially Delivered",
    ],
    "Shipped": [
        "Send To erp",
        "Shipped",
        "Partially Shipped",
        "Delivered",
        "Partially Delivered",
    ],
    "Partially Shipped": [
        "Send To erp",
        "Shipped",
        "Partially Shipped",
        "Delivered",
        "Partially Delivered",
    ],
    "Partially Delivered": [
        "Send To erp",
        "Shipped",
        "Partially Shipped",
        "Delivered",
        "Partially Delivered",
    ],
    "Delivered": [],
}
OSCAR_ORDER_STATUS_CASCADE = {"order": "delivered"}
OSCAR_INITIAL_LINE_STATUS = ""
OSCAR_LINE_STATUS_PIPELINE = {
    "": ("Being processed", "Cancelled", "Completed"),
    "Being processed": (
        "Processed",
        "Cancelled",
    ),
    "Cancelled": (),
    "Processed": (),
}


MIDDLEWARE = [
     'debug_toolbar.middleware.DebugToolbarMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "oscar.apps.basket.middleware.BasketMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
    "role_permission.middleware.CheckRequestURLMiddleware",
    # "role_permission.middleware.AddQuerySetToResponseMiddleware",
    # 'role_permission.middleware.RequestMiddleware',
     
]

def show_toolbar(request):
    return True
SHOW_TOOLBAR_CALLBACK = show_toolbar

INTERNAL_IPS = ['127.0.0.1',]



ROOT_URLCONF = "oneup_project.urls"
# LOGIN_URL = '/store/accounts/login/'
OSCAR_DEFAULT_CURRENCY = "INR"


def location(x):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", x)


# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [
#             location('templates'),
#         ],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            location("templates"),  # templates directory of the project
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": DEBUG,
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "oneup_project.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# DATABASES = {
#      'default': {
#          'ENGINE': 'django.db.backends.mysql',
#          'NAME': 'oscar_oneup',
#          'USER':'oneup',
#          'PASSWORD':'ONEUP_admin',
#          'PORT': '3306'
#      }
# }


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql', # Database engine
#         'NAME': 'test',              # Database name
#         'USER': 'pranav',              # Database user
#         'PASSWORD': 'pranav#123',      # Database password
#         'HOST': 'localhost',                       # Database host (default: 'localhost')
#         'PORT': '5432',                            # Database port (default: '5432')
#     }
# }


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",  # Database engine
        "NAME": config('DATABASE_DB'),  # Database name
        "USER":config('DATABASE_USER') ,  # Database user
        "PASSWORD": config('DB_PASS'),  # Database password
        "HOST": config('DB_URL'),  # Database host (default: 'localhost')
        "PORT": "5432",  # Database port (default: '5432')
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"


USE_I18N = True

USE_TZ = True



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

STATIC_URL = "/static/"
# STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
STATICFILES_DIRS = (os.path.join("static"),)
TINYMCE_JS_URL = os.path.join(STATIC_URL, "path/to/tiny_mce/tiny_mce.js")
TINYMCE_DEFAULT_CONFIG = {
    "cleanup_on_startup": True,
    "custom_undo_redo_levels": 20,
    "selector": "textarea",
    "theme": "silver",
    "plugins": """
            textcolor save link image media preview codesample contextmenu
            table code lists fullscreen  insertdatetime  nonbreaking
            contextmenu directionality searchreplace wordcount visualblocks
            visualchars code fullscreen autolink lists  charmap print  hr
            anchor pagebreak
            """,
    "toolbar1": """
            fullscreen preview bold italic underline | fontselect,
            fontsizeselect  | forecolor backcolor | alignleft alignright |
            aligncenter alignjustify | indent outdent | bullist numlist table |
            | link image media | codesample |
            """,
    "toolbar2": """
            visualblocks visualchars |
            charmap hr pagebreak nonbreaking anchor |  code |
            """,
    "contextmenu": "formats | link image",
    "menubar": True,
    "statusbar": True,
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.simple_backend.SimpleEngine",
    },
}


HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.solr_backend.SolrEngine",
        "URL": "http://127.0.0.1:8983/solr",
        "INCLUDE_SPELLING": True,
    },
}

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.solr_backend.SolrEngine",
        "ENGINE": "haystack.backends.simple_backend.SimpleEngine",
        "URL": "http://127.0.0.1:8983/solr/sandbox",
        "INCLUDE_SPELLING": True,
    },
}
try:
    from oneup_project.local_settings import *
except ImportError as e:
    print("Error", e)
    pass

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = "smtp.gmail.com"
# EMAIL_PORT = 587
# # EMAIL_HOST_USER = "pranavpranab@gmail.com"
# # EMAIL_HOST_PASSWORD = "oqdnjgjarlbjhkvs"
# EMAIL_HOST_USER = "as1816444@gmail.com"
# EMAIL_HOST_PASSWORD = "bmzfgziqszqggjok"
# EMAIL_USE_TLS = True
# API_KEY = "cf937443-7026-11ee-addf-0200cd936042"

EMAIL_HOST = "smtp.zeptomail.in"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "noreply@oneupbrands.com"
EMAIL_HOST_PASSWORD = "PHtE6r0FROi62jR69UUE5fK4RcXwYN99+Og1elFAttkQW/cBTk0Eo95/lmXh/hh8B/NAHaHKnd9tuLrItb2GJGbuNzweXWqyqK3sx/VYSPOZsbq6x00fsFoTcUbVU4TsctNs0y3VutzYNA=="
ORDER_HOST = "orders@oneupbrands.com"
MAIL_HOST_INFO = "noreply@oneupbrands.com"
# EMAIL_HOST_USER = "as1816444@gmail.com"
# EMAIL_HOST_PASSWORD = "bmzfgziqszqggjok"

# API_KEY = "emailapikey"

"""FSHIP API SIGNATURE"""

FSIP_API_SIGNATURE = "085c36066064af83c66b9dbf44d190d40feec79f437bc1c1cb"
RATE_CALCULATOR_URL = "https://capi-qc.fship.in/api/RateCalculator"
user_id_forget = None
React_API_URl = f"https://dev.oneupbrands.com/verify-otp/"


# settings.py

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
         "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "log", "log.log"),
            "formatter": "verbose",
            "maxBytes": 20 * 1024 * 1024, 
            "backupCount": 100,  
        },
         "error_file": {  
            "class": "logging.FileHandler",
            "filename": f"{BASE_DIR}/log/error.log",
            "formatter": "verbose",
            "level": "ERROR", 
        },
        "info_file": { 
            "class": "logging.FileHandler",
            "filename": f"{BASE_DIR}/log/info.log",
            "formatter": "verbose",
            "level": "INFO",  
        },
    },
    "root": {
        "handlers": ["console", "file","error_file","info_file"],
        "level": "DEBUG",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file","error_file",'info_file'],
            "level": "ERROR",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console", "file","error_file",'info_file'],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 20  # 20 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 20  # 20 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 20000000000000000000000000000000000000

CELERY_BROKER_URL = "redis://localhost:6379/0"  # or use your Redis/RabbitMQ URL
CELERY_RESULT_BACKEND = "redis://localhost:6379/1"  # or use your Redis/RabbitMQ URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"


""""everything related erp comes after this """

ERP_URL = config('ERP_URL')
ERP_TOKEN = config('ERP_TOKEN')


REACT_URL = "https://oneupbrands.com/"

RAZORPAY_KEY_ID = config('RAZORPAY_KEY_ID')
RAZORPAY_SECRET_KEY = config('RAZORPAY_SECRET_KEY')