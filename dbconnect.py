import MySQLdb
try:
    import urlparse
except ModuleNotFoundError:
    from urllib import parse as urlparse
import os

urlparse.uses_netloc.append('mysql')

try:
    if 'DATABASES' not in locals():
        DATABASES = {}

    if 'DATABASE_URL' in os.environ:
        url = urlparse.urlparse(os.environ['DATABASE_URL'])

        # Ensure default database exists.
        DATABASES['default'] = DATABASES.get('default', {})

        # Update with environment configuration.
        DATABASES['default'].update({
            'NAME': url.path[1:],
            'USER': url.username,
            'PASSWORD': url.password,
            'HOST': url.hostname,
            'PORT': url.port,
        })

        if url.scheme == 'mysql':
            DATABASES['default']['ENGINE'] = 'django.db.backends.mysql'
except Exception:
    print('Unexpected error:', sys.exc_info())


def connection():
    conn = MySQLdb.connect(host=DATABASES['default']['HOST'],
                           user=DATABASES['default']['USER'],
                           passwd=DATABASES['default']['PASSWORD'],
                           db=DATABASES['default']['NAME']
                           )
    c = conn.cursor()
    return c, conn
