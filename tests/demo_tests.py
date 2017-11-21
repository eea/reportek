import pytest
from faker import Faker

from reportek.core.models import (
    Country,
    ObligationGroup,
    Envelope,
)

fake = Faker()


def fake_name(prefix):
    return f'{prefix}{fake.ean8()}'


@pytest.fixture
def fix_country_at():
    return Country.objects.get(iso='AT')


@pytest.fixture
def fix_og_pass_qa():
    """An obligation group fixture set up for QA auto-pass"""
    og = ObligationGroup.objects.create(
        slug=fake_name('og-'),
        name=fake_name('Obligation Group '),
        workflow_class='reportek.core.models.workflows.demo_auto_qa.DemoPassQAWorkflow')
    return og


@pytest.fixture
def fix_env_pass_qa(fix_og_pass_qa, fix_country_at):
    """An envelope fixture set up for QA auto-pass"""
    env = Envelope(
        slug=fake_name('env-'),
        name=fake_name('Envelope '),
        country=fix_country_at,
        obligation_group=fix_og_pass_qa,
        reporting_period=('2017-01-01', '2017-12-31')
    )
    env.save()
    return env


@pytest.fixture
def fix_og_fail_qa():
    """An obligation group fixture set up for QA auto-fail"""
    og = ObligationGroup.objects.create(
        slug=fake_name('og-'),
        name=fake_name('Obligation Group '),
        workflow_class='reportek.core.models.workflows.demo_auto_qa.DemoFailQAWorkflow')
    return og


@pytest.fixture
def fix_env_fail_qa(fix_og_fail_qa, fix_country_at):
    """An envelope fixture set up for QA auto-pass"""
    env = Envelope(
        slug=fake_name('env-'),
        name=fake_name('Envelope '),
        country=fix_country_at,
        obligation_group=fix_og_fail_qa,
        reporting_period=('2017-01-01', '2017-12-31')
    )
    env.save()
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


def test_envelope_workflow_assignment(fix_env_pass_qa):
    """Check workflow presence on new envelope"""
    assert fix_env_pass_qa.workflow.type == 'core.demopassqaworkflow'


def test_envelope_auto_pass_qa(fix_env_pass_qa):
    """Check auto QA pass into 'review' state"""
    fix_env_pass_qa.workflow.xwf.send_to_qa()
    assert fix_env_pass_qa.workflow.current_state == 'review'


def test_envelope_auto_fail_qa(fix_env_fail_qa):
    """Check auto QA fail into 'draft' state"""
    fix_env_fail_qa.workflow.xwf.send_to_qa()
    assert fix_env_fail_qa.workflow.current_state == 'draft'


def test_e2e_workflow(fix_env_pass_qa):
    """Walk through the auto-pass QA workflow to the end state"""
    assert fix_env_pass_qa.workflow.current_state == 'draft'
    fix_env_pass_qa.workflow.xwf.send_to_qa()
    assert fix_env_pass_qa.workflow.current_state == 'review'
    fix_env_pass_qa.workflow.xwf.reject()
    assert fix_env_pass_qa.workflow.current_state == 'draft'
    fix_env_pass_qa.workflow.xwf.send_to_qa()
    assert fix_env_pass_qa.workflow.current_state == 'review'
    fix_env_pass_qa.workflow.xwf.accept()
    assert fix_env_pass_qa.workflow.current_state == 'end'
    assert fix_env_pass_qa.finalized
