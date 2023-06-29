# WorkWhere

WorkWhere is a web-based Django app for workplace reservations. It is kept very simple and best suited for small enterprises.

Detailed documentation is (not yet) stored in the "docs" directory.

## Installation

Clone the WorkWhere app from Github. 
In the terminal, go to the repository of your Django page. If you don't have a Django page yet, follow the [Django tutorial](https://docs.djangoproject.com/en/4.1/intro/tutorial01/#creating-a-project) to create your own project.

Next, install the WorkWhere app and its requirements by

```
pip install [-e] path/to/workwhere
```

Use the `-e` option if you are a developer and add changes to the application. 

## Quick start

This section explains how to integrate the WorkWhere app into your Django website, after successfull installation.

### 1. Add "workwhere" to your INSTALLED_APPS setting.

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

### 2. Include the WorkWhere URLconf in your project urls.py

```python
path('workwhere/', include('workwhere.urls')),
```

For development also add the lines

```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 
```

### 3. Create the workhwere models

    python manage.py migrate

### 4. Start the server

For development use the `DEBUG = TRUE` setting. Start the development server by

    python manage.py runserver

Visit http://127.0.0.1:8000/admin/ to create employees and workplaces (you'll need the Admin app enabled) and http://127.0.0.1:8000/workwhere/ to use the app.

For production set `DEBUG = False` and run your production server, like. e.g. nginx and gunicorn.

