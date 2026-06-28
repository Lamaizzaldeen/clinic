
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkshopViewSet

router = DefaultRouter()
router.register('', WorkshopViewSet, basename='workshops')

urlpatterns = [
    path('', include(router.urls)),
]
