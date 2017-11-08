from django.db import models
import xworkflows as xwf


class WorkFlow(models.Model):
    name = models.CharField(max_length=30, unique=True)

    class Meta:
        verbose_name = 'workflow'
        verbose_name_plural = 'workflows'

    def __str__(self):
        return self.name

    def make_xworkflow_cls(self, log_transitions=False):

        # noinspection PyUnusedLocal
        def dont_log_transition(self, *args, **kwargs):
            pass

        states = ((s.name, s.title) for s in self.states.all())
        transitions = (
            (t.name, (src.state.name for src in t.sources.all()), t.target.name)
            for t in self.transitions.all()
        )
        initial_state = self.initial_state.first().state.name

        bases = (xwf.Workflow,)
        attrs = {
            'states': states,
            'transitions': transitions,
            'initial_state': initial_state
        }

        if not log_transitions:
            attrs['log_transition'] = dont_log_transition

        return type(self.name, bases, attrs)


class WFState(models.Model):
    name = models.CharField(max_length=30)
    title = models.CharField(max_length=100)
    workflow = models.ForeignKey(WorkFlow, related_name='states')

    class Meta:
        verbose_name = 'workflow state'
        verbose_name_plural = 'workflow states'
        unique_together = ('name', 'workflow')

    def __str__(self):
        return f'{self.title} ({self.name}) [{self.workflow}]'


class WFInitialState(models.Model):
    """
    The unfortunate consequence of Django missing support for
    both composite PKs and deferrable constraints:

     - no deferrables means a non-nullable FK to WFState cannot exist on WorkFlow
     - no CPK means we can't simply have PK(WorkFlow FK, WFState FK) here.
    """
    workflow = models.ForeignKey(WorkFlow, primary_key=True, related_name='initial_state')
    state = models.ForeignKey(WFState, unique=True)

    class Meta:
        verbose_name = 'workflow initial state'
        verbose_name_plural = 'workflow initial states'

    def __str__(self):
        return f'{self.state.name} ({self.workflow.name})'


class WFTransition(models.Model):
    name = models.CharField(max_length=30)
    workflow = models.ForeignKey(WorkFlow, related_name='transitions')
    target = models.ForeignKey(WFState)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'workflow transition'
        verbose_name_plural = 'workflow transitions'
        unique_together = ('name', 'workflow')
        

class WFTransitionSource(models.Model):
    transition = models.ForeignKey(WFTransition, related_name='sources')
    state = models.ForeignKey(WFState)

    def __str__(self):
        return f'{self.state.name} [{self.transition.name}]'

    class Meta:
        unique_together = ('transition', 'state')
        verbose_name = 'workflow transition source'
        verbose_name_plural = 'workflow transition sources'
