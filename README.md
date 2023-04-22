# django-workwhere

WorkWhere is a simple web-based Django app for workplace reservations.

Detailed documentation is in the "docs" directory.

## Installation

In the terminal, go to the repository of your django page. Install the django app by

```
pip install [-e] path/to/django-workwhere
```

Use the `-e` option if you are a developer and add changes to the application. 

## Quick start

1. Add "workwhere" to your INSTALLED_APPS setting like this:

```python
    INSTALLED_APPS = [
        ...
        'workwhere',
    ]
```

And if you didn't specify media locations yet, add the lines

```python
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"
```

2. Include the workwhere URLconf in your project urls.py like this::

```python
    path('workwhere/', include('workwhere.urls')),
```

And for development also add the lines

```python
    if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 
```

3. Run ``python manage.py migrate`` to create the workhwere models.

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to create employees and workplaces (you'll need the Admin app enabled).

5. Visit http://127.0.0.1:8000/workwhere/ to start.