from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('predict/<str:steel_type>/', views.predict_view, name='predict'),
    path('history/<str:steel_type>/', views.history_view, name='history'),
]
