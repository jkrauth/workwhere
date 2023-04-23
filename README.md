# WorkWhere

WorkWhere is a web-based Django app for workplace reservations. It is kept very simple and best suited for small enterprises.

Detailed documentation is in the "docs" directory.

## Installation

In the terminal, go to the repository of your django page. Install the django app by

```
pip install [-e] path/to/django-workwhere
```

Use the `-e` option if you are a developer and add changes to the application. 

## Quick start

Skip the first step if you already have a Django project running and just want to integrate this app into it.

### 1. Create a Django project. 

You find help [here](https://docs.djangoproject.com/en/4.1/intro/tutorial01/#creating-a-project).

### 2. Add "workwhere" to your INSTALLED_APPS setting.

```python
INSTALLED_APPS = [
    ...
    'workwhere',
]
```

If you didn't specify media locations yet, add the lines

```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

### 3. Include the workwhere URLconf in your project urls.py

```python
path('workwhere/', include('workwhere.urls')),
```

For development also add the lines

```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 
```

### 4. Create the workhwere models

    python manage.py migrate

### 5. Start the server

For development use the `DEBUG = TRUE` setting. Start the development server by

    python manage.py runserver

Visit http://127.0.0.1:8000/admin/ to create employees and workplaces (you'll need the Admin app enabled).

For production set `DEBUG = False` and run

    python manage.py runserver <your ip address>:<port number>

### 6. Visit http://127.0.0.1:8000/workwhere/.

