"""

**DEPRECATED**

Use :mod:`celery.defaults` instead.


"""
from celery import current_app
from celery.app import defaults

_DEFAULTS = defaults.DEFAULTS
conf = current_app.conf

ALWAYS_EAGER = conf.CELERY_ALWAYS_EAGER
EAGER_PROPAGATES_EXCEPTIONS = conf.CELERY_EAGER_PROPAGATES_EXCEPTIONS
RESULT_BACKEND = conf.CELERY_RESULT_BACKEND
CACHE_BACKEND = conf.CELERY_CACHE_BACKEND
CACHE_BACKEND_OPTIONS = conf.CELERY_CACHE_BACKEND_OPTIONS
TASK_SERIALIZER = conf.CELERY_TASK_SERIALIZER
TASK_RESULT_EXPIRES = conf.CELERY_TASK_RESULT_EXPIRES
IGNORE_RESULT = conf.CELERY_IGNORE_RESULT
TRACK_STARTED = conf.CELERY_TRACK_STARTED
ACKS_LATE = conf.CELERY_ACKS_LATE
REDIRECT_STDOUTS = conf.CELERY_REDIRECT_STDOUTS
REDIRECT_STDOUTS_LEVEL = conf.CELERY_REDIRECT_STDOUTS_LEVEL
RESULT_DBURI = conf.CELERY_RESULT_DBURI
RESULT_ENGINE_OPTIONS = conf.CELERY_RESULT_ENGINE_OPTIONS
MAX_CACHED_RESULTS = conf.CELERY_MAX_CACHED_RESULTS
SEND_EVENTS = conf.CELERY_SEND_EVENTS
DEFAULT_RATE_LIMIT = conf.CELERY_DEFAULT_RATE_LIMIT
DISABLE_RATE_LIMITS = conf.CELERY_DISABLE_RATE_LIMITS
CELERYD_TASK_TIME_LIMIT = conf.CELERYD_TASK_TIME_LIMIT
CELERYD_TASK_SOFT_TIME_LIMIT = conf.CELERYD_TASK_SOFT_TIME_LIMIT
CELERYD_MAX_TASKS_PER_CHILD = conf.CELERYD_MAX_TASKS_PER_CHILD
STORE_ERRORS_EVEN_IF_IGNORED = conf.CELERY_STORE_ERRORS_EVEN_IF_IGNORED
CELERY_SEND_TASK_ERROR_EMAILS = conf.CELERY_SEND_TASK_ERROR_EMAILS
CELERY_TASK_ERROR_WHITELIST = conf.CELERY_TASK_ERROR_WHITELIST
CELERYD_LOG_FORMAT = conf.CELERYD_LOG_FORMAT
CELERYD_TASK_LOG_FORMAT = conf.CELERYD_TASK_LOG_FORMAT
CELERYD_LOG_FILE = conf.CELERYD_LOG_FILE
CELERYD_LOG_COLOR = conf.CELERYD_LOG_COLOR
CELERYD_LOG_LEVEL = conf.CELERYD_LOG_LEVEL
CELERYD_STATE_DB = conf.CELERYD_STATE_DB
CELERYD_CONCURRENCY = conf.CELERYD_CONCURRENCY
CELERYD_PREFETCH_MULTIPLIER = conf.CELERYD_PREFETCH_MULTIPLIER
CELERYD_POOL_PUTLOCKS = conf.CELERYD_POOL_PUTLOCKS
CELERYD_POOL = conf.CELERYD_POOL
CELERYD_LISTENER = conf.CELERYD_CONSUMER
CELERYD_MEDIATOR = conf.CELERYD_MEDIATOR
CELERYD_ETA_SCHEDULER = conf.CELERYD_ETA_SCHEDULER
CELERYD_ETA_SCHEDULER_PRECISION = conf.CELERYD_ETA_SCHEDULER_PRECISION
ADMINS = conf.ADMINS
SERVER_EMAIL = conf.SERVER_EMAIL
EMAIL_HOST = conf.EMAIL_HOST
EMAIL_HOST_USER = conf.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = conf.EMAIL_HOST_PASSWORD
EMAIL_PORT = conf.EMAIL_PORT
BROKER_HOST = conf.BROKER_HOST
BROKER_PORT = conf.BROKER_PORT
BROKER_USER = conf.BROKER_USER
BROKER_PASSWORD = conf.BROKER_PASSWORD
BROKER_VHOST = conf.BROKER_VHOST
BROKER_USE_SSL = conf.BROKER_USE_SSL
BROKER_INSIST = conf.BROKER_INSIST
BROKER_CONNECTION_TIMEOUT = conf.BROKER_CONNECTION_TIMEOUT
BROKER_CONNECTION_RETRY = conf.BROKER_CONNECTION_RETRY
BROKER_CONNECTION_MAX_RETRIES = conf.BROKER_CONNECTION_MAX_RETRIES
BROKER_BACKEND = conf.BROKER_TRANSPORT
DEFAULT_QUEUE = conf.CELERY_DEFAULT_QUEUE
DEFAULT_ROUTING_KEY = conf.CELERY_DEFAULT_ROUTING_KEY
DEFAULT_EXCHANGE = conf.CELERY_DEFAULT_EXCHANGE
DEFAULT_EXCHANGE_TYPE = conf.CELERY_DEFAULT_EXCHANGE_TYPE
DEFAULT_DELIVERY_MODE = conf.CELERY_DEFAULT_DELIVERY_MODE
QUEUES = conf.CELERY_QUEUES
CREATE_MISSING_QUEUES = conf.CELERY_CREATE_MISSING_QUEUES
ROUTES = conf.CELERY_ROUTES
BROADCAST_QUEUE = conf.CELERY_BROADCAST_QUEUE
BROADCAST_EXCHANGE = conf.CELERY_BROADCAST_EXCHANGE
BROADCAST_EXCHANGE_TYPE = conf.CELERY_BROADCAST_EXCHANGE_TYPE
EVENT_SERIALIZER = conf.CELERY_EVENT_SERIALIZER
RESULT_EXCHANGE = conf.CELERY_RESULT_EXCHANGE
RESULT_EXCHANGE_TYPE = conf.CELERY_RESULT_EXCHANGE_TYPE
RESULT_SERIALIZER = conf.CELERY_RESULT_SERIALIZER
RESULT_PERSISTENT = conf.CELERY_RESULT_PERSISTENT
CELERYBEAT_LOG_LEVEL = conf.CELERYBEAT_LOG_LEVEL
CELERYBEAT_LOG_FILE = conf.CELERYBEAT_LOG_FILE
CELERYBEAT_SCHEDULER = conf.CELERYBEAT_SCHEDULER
CELERYBEAT_SCHEDULE = conf.CELERYBEAT_SCHEDULE
CELERYBEAT_SCHEDULE_FILENAME = conf.CELERYBEAT_SCHEDULE_FILENAME
CELERYBEAT_MAX_LOOP_INTERVAL = conf.CELERYBEAT_MAX_LOOP_INTERVAL
CELERYMON_LOG_LEVEL = conf.CELERYMON_LOG_LEVEL
CELERYMON_LOG_FILE = conf.CELERYMON_LOG_FILE
