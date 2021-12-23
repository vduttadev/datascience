from django.urls import path

from . import views
# from rest_framework_simplejwt.views import (
#    TokenObtainPairView,
#    TokenRefreshView,
#    TokenVerifyView
# )

urlpatterns = [
    path('control-panel-service/api/v1/bind-plans', views.bind_plan, name='bind_plan'),
    path('control-panel-service/health', views.isAlive, name='isAliveService')
]
