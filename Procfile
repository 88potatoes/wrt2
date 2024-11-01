web: gunicorn wrt2.wsgi
release: python manage.py migrate --database="turso"
worker-api: celery -A wrt2 worker --loglevel=info
