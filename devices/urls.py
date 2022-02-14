from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('help/', views.help_page),
    path('add_device/', views.add_device, name='add-device')
]
