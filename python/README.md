# Django REST Framework

1. Got a working example up and running by following the instructions [here](https://scotch.io/tutorials/build-a-rest-api-with-django-a-test-driven-approach-part-1).

2. Integrated the [`drf-yasg`](https://github.com/axnsan12/drf-yasg/) plugin by following the instructions [here](https://drf-yasg.readthedocs.io/en/stable/readme.html#installation)

### Install

```
cd ./django
python3 -m venv ./venv
source venv/bin/activate
pip install -r requirements.txt
cd ./djangorest
```

### Apply database migrations

```
./manage.py migrate
```

### Run tests

```
./manage.py test
```

### Start server

```
./manage.py runserver
```
