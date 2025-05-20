from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import GVGDataParser

from . import views

urlpatterns = [
    path('gvg/data/parse/', GVGDataParser.as_view()),
]
