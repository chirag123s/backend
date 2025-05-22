# django_app/carreb/api/urls.py
from django.urls import path, include, re_path
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views import (
    PraseCDGG, StateListView, GetCarMakesListView, GetCarModelListView, 
    GetCarYearListView, GetCarEngineTypeListView, CarVariantListView, 
    CarSeriesListView, CarMatchesListView, CarSuggestionListView,
    TestAuthView, TestPublicView
)
from . import views

schema_view = get_schema_view(
    openapi.Info(
        title="Carreb API",
        default_version='v1',
        description="API documentation with Swagger UI - Now with Auth0 Authentication",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # File parsing endpoint (protected)
    path('parse-cd-gg/', PraseCDGG.as_view(), name='parse_cd_gg'),
    
    # Public endpoints
    path('states/', StateListView.as_view(), name='states'),
    
    # Protected car data endpoints
    path('car/makes/', GetCarMakesListView.as_view(), name='car_makes'),
    path('car/models/', GetCarModelListView.as_view(), name='car_models'),
    path('car/years/', GetCarYearListView.as_view(), name='car_years'),
    path('car/engine-types/', GetCarEngineTypeListView.as_view(), name='car_engine_types'),
    path('car/variants/', CarVariantListView.as_view(), name='car_variants'),
    path('car/series/', CarSeriesListView.as_view(), name='car_series'),
    path('car/matches/', CarMatchesListView.as_view(), name='car_matches'),
    path('car/suggestions/', CarSuggestionListView.as_view(), name='car_suggestions'),
    
    # Authentication test endpoints
    path('test/auth/', TestAuthView.as_view(), name='test_auth'),
    path('test/public/', TestPublicView.as_view(), name='test_public'),
    
    # Payment endpoints
    path('payment/', include('payments.urls')),

    # API Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]