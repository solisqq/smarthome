from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('requests', views.requestsf, name='requests'),
    path('trigger/<int:id>', views.trigger, name='trigger'),
]