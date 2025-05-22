from django.urls import path, include, re_path
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views import PraseCDGG, StateListView, GetCarMakesListView, GetCarModelListView, GetCarYearListView, GetCarEngineTypeListView, CarVariantListView, CarSeriesListView, CarMatchesListView, CarSuggestionListView
from . import views

schema_view = get_schema_view(
    openapi.Info(
        title="Carreb API",
        default_version='v1',
        description="API documentation with Swagger UI",
        #terms_of_service="https://www.example.com/terms/",
        #contact=openapi.Contact(email="support@example.com"),
        #license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    #permission_classes=(permissions.IsAuthenticated,)
)

urlpatterns = [
    path('parse-cd-gg/', PraseCDGG.as_view(), name='parse_cd_gg'),
    path('states/', StateListView.as_view()),
    path('car/makes/', GetCarMakesListView.as_view()),
    #path('car/<str:make_name>/models/', CarModelListView.as_view()),
    path('car/models/', GetCarModelListView.as_view()),
    path('car/years/', GetCarYearListView.as_view()),
    path('car/engine-types/', GetCarEngineTypeListView.as_view()),
    #path('car/<str:make_name>/<str:model_name>/variants/', CarVariantListView.as_view()),
    path('car/variants/', CarVariantListView.as_view()),
    path('car/series/', CarSeriesListView.as_view()),
    path('car/matches/', CarMatchesListView.as_view()),
    path('car/suggestions/', CarSuggestionListView.as_view()),

    path('payment/', include('payments.urls')),

    # Swagger UI:
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    # Redoc (optional):
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
