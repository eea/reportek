from django.db import models
import xworkflows as xwf


class WorkFlow(models.Model):
    name = models.CharField(max_length=30)
    # Initial state is nullable to avoid circular FK
    # issues in admin
    initial_state = models.ForeignKey(
        'WFState',
        related_name='workflows_initiated',
        blank=True, null=True,
    )

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
        initial_state = self.initial_state.name

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

    def __str__(self):
        return f'{self.title} ({self.name}) [{self.workflow}]'


class WFTransition(models.Model):
    name = models.CharField(max_length=30)
    workflow = models.ForeignKey(WorkFlow, related_name='transitions')
    target = models.ForeignKey(WFState)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'workflow transition'
        verbose_name_plural = 'workflow transitions'


class WFTransitionSource(models.Model):
    transition = models.ForeignKey(WFTransition, related_name='sources')
    state = models.ForeignKey(WFState)

    def __str__(self):
        return f'{self.state.name} [{self.transition.name}]'

    class Meta:
        unique_together = ('transition', 'state')
        verbose_name = 'workflow transition source'
        verbose_name_plural = 'workflow transition sources'
