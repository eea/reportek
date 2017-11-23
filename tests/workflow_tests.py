import pytest

from datetime import date

from reportek.core.models import (
    Country,
    ObligationGroup,
    Envelope,
)

from .common import fake_name


@pytest.fixture
def fix_og_pass_qa(request):
    """An obligation group fixture set up for QA auto-pass"""
    og = ObligationGroup.objects.create(
        slug='og-pass-fix-1',
        name=fake_name('Obligation Group '),
        workflow_class='reportek.core.models.workflows.demo_auto_qa.DemoPassQAWorkflow',
        next_reporting_start=date.today(),
        reporting_duration_months=12,
    )
    og.save()
    og.start_reporting_period()

    def fin():
        og.reporting_period_set.all().delete()
        og.delete()

    request.addfinalizer(fin)

    return og


@pytest.fixture
def fix_env_pass_qa(request, fix_og_pass_qa):
    """An envelope fixture set up for QA auto-pass"""
    country = Country.objects.get(iso='AT')
    og = ObligationGroup.objects.get(id=fix_og_pass_qa.id)
    env = Envelope(
        slug='env-pass-fix-1',
        name=fake_name('Envelope '),
        country=country,
        obligation_group=og,
    )
    env.save()

    def fin():
        env.delete()

    request.addfinalizer(fin)
    return env


@pytest.fixture
def fix_og_fail_qa(request):
    """An obligation group fixture set up for QA auto-fail"""
    og = ObligationGroup.objects.create(
        slug='og-fail-fix-1',
        name=fake_name('Obligation Group '),
        workflow_class='reportek.core.models.workflows.demo_auto_qa.DemoFailQAWorkflow',
        next_reporting_start=date.today(),
        reporting_duration_months=12,
    )
    og.start_reporting_period()
    og.save()

    def fin():
        og.reporting_period_set.all().delete()
        og.delete()

    request.addfinalizer(fin)
    return og


@pytest.fixture
def fix_env_fail_qa(request, fix_og_fail_qa):
    """An envelope fixture set up for QA auto-pass"""
    country = Country.objects.get(iso='AT')
    og = ObligationGroup.objects.get(id=fix_og_fail_qa.id)
    env = Envelope(
        slug='env-fail-fix-1',
        name=fake_name('Envelope '),
        country=country,
        obligation_group=og,
    )
    env.save()

    def fin():
        env.delete()

    request.addfinalizer(fin)
    return env


@pytest.mark.parametrize('wf_class,wf_display', [
    ('reportek.core.models.workflows.demo_auto_qa.DemoAutoQAWorkflow', 'DemoAutoQAWorkflow'),
    ('reportek.core.models.workflows.demo_auto_qa.DemoPassQAWorkflow', 'DemoPassQAWorkflow'),
    ('reportek.core.models.workflows.demo_auto_qa.DemoFailQAWorkflow', 'DemoFailQAWorkflow'),
])
def test_og_wf_display(wf_class, wf_display):
    """Tests display name of obligation group's workflow"""
    og = ObligationGroup.objects.create(
        slug=fake_name('og-'),
        name=fake_name('Obligation Group '),
        workflow_class=wf_class)
    assert og.get_workflow_class_display() == wf_display


@pytest.mark.usefixtures('fix_env_pass_qa')
def test_envelope_workflow_assignment():
    """Check workflow presence on new envelope"""
    env = Envelope.objects.get(slug='env-pass-fix-1')
    assert env.workflow.type == 'core.demopassqaworkflow'


@pytest.mark.usefixtures('fix_env_pass_qa')
def test_envelope_auto_pass_qa():
    """Check auto QA pass into 'review' state"""
    env = Envelope.objects.get(slug='env-pass-fix-1')
    env.workflow.xwf.send_to_qa()
    assert env.workflow.current_state == 'review'


@pytest.mark.usefixtures('fix_env_fail_qa')
def test_envelope_auto_fail_qa():
    """Check auto QA fail into 'draft' state"""
    env = Envelope.objects.get(slug='env-fail-fix-1')
    env.workflow.xwf.send_to_qa()
    assert env.workflow.current_state == 'draft'


@pytest.mark.usefixtures('fix_env_pass_qa')
def test_e2e_workflow():
    """Walk through the auto-pass QA workflow to the end state"""
    env = Envelope.objects.get(slug='env-pass-fix-1')
    assert env.workflow.current_state == 'draft'
    env.workflow.xwf.send_to_qa()
    assert env.workflow.current_state == 'review'
    env.workflow.xwf.reject()
    assert env.workflow.current_state == 'draft'
    env.workflow.xwf.send_to_qa()
    assert env.workflow.current_state == 'review'
    env.workflow.xwf.accept()
    assert env.workflow.current_state == 'end'
    assert env.finalized
