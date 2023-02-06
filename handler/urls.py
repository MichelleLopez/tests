from django.conf.urls import include, url
from handler import views

urlpatterns = [
    url(r'^$', views.handler_none, name='handler-none'),
    url(r'^gracias/$', views.handler_registered, name='handler-gracias'),
    url(r'^h/(?P<click_area>\w+)$', views.handler_home, name='handler-home'),
    url(r'^login/(?P<click_area>\w+)$', views.handler_alfresco, name='handler-alfresco'),
]