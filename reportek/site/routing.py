"""
Channels ASGI application and websocket routing.
"""

from django.conf.urls import url
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack


from reportek.core.consumers import EnvelopeWSConsumer


application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter([
            url('^ws/envelopes/(?P<pk>[0-9]+)$', EnvelopeWSConsumer)
        ])
    )
})
