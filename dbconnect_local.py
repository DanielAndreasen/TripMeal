import MySQLdb
import urlparse
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
    print 'Unexpected error:', sys.exc_info()


def connection():
    # b2988a5c1fbd13:58fba0db@us-cdbr-iron-east-04.cleardb.net/heroku_82f1350681fdb54
    conn = MySQLdb.connect(host='us-cdbr-iron-east-04.cleardb.net',
                           user='b2988a5c1fbd13',
                           passwd='58fba0db',
                           db='heroku_82f1350681fdb54'
                           )
    # conn = MySQLdb.connect(host='localhost',
    #                        user='root',
    #                        passwd='gichin124',
    #                        db='tripmeal'
    #                        )
    c = conn.cursor()
    return c, conn
