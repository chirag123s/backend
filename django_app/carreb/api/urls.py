from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import PraseCDGG, StateListView, CarMakes, CarModelListView, CarVariantListView, CarSeriesListView, CarMatchesListView, CarSuggestionListView

from . import views

urlpatterns = [
    path('parse-cd-gg/', PraseCDGG.as_view(), name='parse_cd_gg'),
    path('states/', StateListView.as_view()),
    path('car/makes/', CarMakes.as_view()),
    #path('car/<str:make_name>/models/', CarModelListView.as_view()),
    path('car/models/', CarModelListView.as_view()),
    #path('car/<str:make_name>/<str:model_name>/variants/', CarVariantListView.as_view()),
    path('car/variants/', CarVariantListView.as_view()),
    path('car/series/', CarSeriesListView.as_view()),
    path('car/matches/', CarMatchesListView.as_view()),
    path('car/suggestions/', CarSuggestionListView.as_view()),
]
