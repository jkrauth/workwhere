from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'workwhere' # Set application namespace
urlpatterns = [
    path('', views.index, name='index'),
    path('reserve/', views.reserve, name='reserve'),
    path('week/', views.WeekRedirect.as_view(), name='week_redirect'),
    path('week/<int:year>/<int:week>/', views.week, name='week'),
    path('today/', views.Today.as_view(), name='today'),
    path('floorplans/', views.Floorplans.as_view(), name='floorplans'),

    path('ajax/update-today', views.Today.as_view(template_name='workwhere/today_list.html'), name='ajax_update_today'),
    path('ajax/load-workplaces/', views.load_workplaces, name='ajax_load_workplaces'),
]