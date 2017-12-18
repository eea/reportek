import pytest

from datetime import date
from rest_framework import status

from django.contrib.auth.models import User

from reportek.core.models import (
    Country,
    ObligationGroup,
    Envelope
)

from reportek.site.urls import API_VERSION

from .common import (
    fake_name,
    api_factory,
    api_client,
    user_credentials,
    user_session,
    forced_auth,
    basic_auth
)


@pytest.fixture
def fix_admin_user():
    admin = User(username='admin', password='admin', is_superuser=True)
    admin.save()


@pytest.fixture
def fix_og(request):
    og = ObligationGroup.objects.create(
        slug='og-fix-1',
        name=fake_name('Obligation Group '),
        workflow_class='reportek.core.models.workflows.demo_auto_qa.DemoPassQAWorkflow',
        next_reporting_start=date.today(),
        reporting_duration_months=12,
        qa_xmlrpc_uri='http://localhost/RpcRouter',
    )
    og.save()
    og.start_reporting_period()

    def fin():
        og.reporting_period_set.all().delete()
        og.delete()

    request.addfinalizer(fin)
    return og


@pytest.fixture
def fix_env(request, fix_og):
    """An envelope fixture set up for QA auto-pass"""
    og = ObligationGroup.objects.get(id=fix_og.id)
    country = Country.objects.get(iso='AT')
    env = Envelope(
        slug='env-fix-1',
        name=fake_name('Envelope '),
        country=country,
        obligation_group=og,
    )
    env.save()

    def fin():
        env.delete()

    request.addfinalizer(fin)

    return env


@pytest.mark.usefixtures('fix_env', 'fix_admin_user')
def test_get_envelope():
    with user_credentials('admin'):
        env = Envelope.objects.get(slug='env-fix-1')
        response = api_client.get(
            path=f'/api/{API_VERSION}/envelopes/{env.id}',
            follow=True,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == env.id
        assert response.data['slug'] == env.slug
        print(response.data)
