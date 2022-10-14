from django.urls import path, include
from rest_framework import routers

from backend import views

router = routers.DefaultRouter()
router.register(r'plants', views.PlantViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
