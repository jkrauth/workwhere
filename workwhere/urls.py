from django.urls import include, path
from django.views.generic import RedirectView

from . import views

app_name = 'workwhere' # Set application namespace
urlpatterns = [
    path('', views.index, name='index'),
    path('week/', views.WeekRedirect.as_view(), name='week_redirect'),
    path('week/<int:year>/<int:week>/', views.week, name='week'),
    path('today/', views.Today.as_view(), name='today'),
    path('info/', views.Info.as_view(), name='info'),

    path('ajax/update-today', views.Today.as_view(template_name='workwhere/today_list.html'), name='ajax_update_today'),
    path('ajax/load-workplaces/', views.load_workplaces, name='ajax_load_workplaces'),

    path('summary/', views.SummaryRedirect.as_view(), name='summary_redirect'),
    path('summary/<int:year>/<int:month>/', views.summary, name='summary'),    
]
