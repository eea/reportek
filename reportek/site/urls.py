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
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework.documentation import include_docs_urls

from . import api_urls
from . import views


API_VERSION = "0.1"


_country = r'(?P<country>[a-z]{2})'
_instrument = r'(?P<instrument>[\w-]+)'
_obligation = r'(?P<obligation>[\w-]+)'

urlpatterns = [
    # TODO: this is starting to get messy, the namespacing needs some love.
    url(r'^', include('reportek.core.frontend.urls', namespace='core')),

    url(r'^admin/', admin.site.urls),
    url(r'^$',
        views.home, name='home'),
    url(f'^{ _country }/$',
        views.country, name='country'),
    url(f'^{ _country }/{ _instrument }/$',
        views.instrument, name='instrument'),
    url(f'^{ _country }/{ _instrument }/{ _obligation }/$',
        views.obligation, name='obligation'),

    url(r'^api/%s/' % API_VERSION, include(api_urls, namespace='api')),
    url(r'^docs/', include_docs_urls(title='Reportek API Documentation', public=False)),
]
