from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import GVGDataParser
from .views_cars import DownloadCarImageFromDDG

from . import views

urlpatterns = [
    path('gvg/data/parse/', GVGDataParser.as_view()),
    path('ddg/dl/cars/', DownloadCarImageFromDDG.as_view()),
]
