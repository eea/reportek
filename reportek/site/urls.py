"""reportek_site URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/

Examples:

Function views:
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')

Class-based views:
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')

Including another URLconf:
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework.documentation import include_docs_urls

from ..core.api import urls as api_urls
from .views import spabundle


API_VERSION = '0.1'


urlpatterns = [
    url(r'^api/%s/' % API_VERSION, include(api_urls, namespace='api')),
    url(r'^admin/', admin.site.urls),
    url(r'^api-docs/', include_docs_urls(title='Reportek API Documentation', public=False)),
]

if settings.DEBUG:
    # Enable Browsable API login/logout
    urlpatterns.append(
        url(r'^api-auth/', include('rest_framework.urls'))
    )
    try:
        import debug_toolbar
    except ImportError:
        pass
    else:
        urlpatterns.append(
            url(r'^__debug__/', include(debug_toolbar.urls))
        )

# Add the SPA catch-all route last
urlpatterns += [
    url(r'^', spabundle, name='spa'),
]
