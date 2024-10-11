web: gunicorn wrt2.wsgi
release: python manage.py migrate --database="turso"
worker-1: celery -A wrt2 worker -Q app1_queue --loglevel=info
