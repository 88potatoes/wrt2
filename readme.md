How to set up the environment

First pip install the requirements
```shell
pip install -r requirements.txt
```

Then create a .env files in the root directory and add the following lines
```
DEBUG=True
DJANGO_SECRET_KEY=zyd7_me&l#6vyajc+f40nt%6zo_s_09k1prm0izive)w1edkv7
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

If you need to remake the the db.sqlite3 file, then you need to run `python manage.py migrate`. 
Then run `python manage.py createsuperuser` and create a new user that you can log in with.