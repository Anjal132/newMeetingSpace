"""meetingSpace URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework.schemas import get_schema_view
from rest_framework.documentation import include_docs_urls
from rest_framework import permissions
from drf_yasg.views import get_schema_view as get_schema
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static

schema_view = get_schema(
   openapi.Info(
      title="Meeting Space API",
      default_version='v1',
      description="This is the api docs of the meeting space api",
   ),
   public=True,
   authentication_classes=(),
   permission_classes=(permissions.AllowAny,),
)

SCHEMA_VIEWS = get_schema_view(title="Meeting Space")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('api.urls')),
    path('schema/', SCHEMA_VIEWS),
    path('docs/', include_docs_urls(title="Meeting Space")),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
