import re
import logging
from functools import partial
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.contrib.contenttypes.fields import GenericRelation
from typedmodels.models import TypedModel
import xworkflows as xwf
import pygraphviz as gv


from reportek.core.tasks import submit_xml_to_qa
from .log import TransitionEvent


log = logging.getLogger('reportek.workflows')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


class BaseWorkflow(TypedModel):
    """
    Base class for workflows.
    Workflows are implemented as concrete types based on this.
    """

    name = models.CharField(max_length=100)
    previous_state = models.CharField(max_length=60, null=True, blank=True)
    current_state = models.CharField(max_length=60, null=True, blank=True)
    history = GenericRelation(TransitionEvent)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_workflow'
        verbose_name = 'workflow'

    class TransitionDoesNotExist(Exception):
        pass

    class TransitionNotAvailable(Exception):
        pass

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.current_state = self.current_state or self.initial_state
        super().save(*args, **kwargs)

    # Concrete types must specify these per the XWorkflows API
    states = ()
    transitions = ()
    initial_state = None
    final_state = None
    upload_states = []

    @property
    def finished(self):
        return self.current_state == self.final_state

    @property
    def upload_allowed(self):
        return self.current_state in self.upload_states

    @property
    def available_transitions(self):
        state = self.xwf.state.workflow.states[self.current_state]
        return [
            t.name
            for t in self.xwf.state.workflow.transitions
            if state.name in [s.name for s in t.source]
        ]

    def submit_xml_to_qa(self):
        """
        Sends the envelope to QA, providing the result callback.
        """
        return submit_xml_to_qa(self.envelope.pk)

    def handle_auto_qa_results(self, *args, **kwargs):
        """
        Concrete types must implement this with the post-QA logic
        (i.e. to trigger an automatic transition).
        """
        raise NotImplementedError

    @cached_property
    def xwf_cls_name(self):
        """Builds a cleaned-up name for the XWorkflow class"""
        pattern = re.compile('[\W_]+')
        return f'XWFDef_{re.sub(pattern, "", self.name.capitalize())}'

    @property
    def xwf_cls(self):
        """
        Builds a custom XWorkflow class from the concrete type's specs.
        """
        def log_transition(self, transition, from_state, workflow):
            """
            Transition event logger - supplied to the XWorkflow class.
            """
            trans, src, dst = transition.name, from_state, workflow.state
            info(f'Logging transition "{trans}"')
            TransitionEvent.objects.create(
                content_object=self.bearer,
                transition=trans,
                from_state=src,
                to_state=dst
            )
            info(f'"{self.bearer.envelope.name}" is now in state "{dst}".')

        bases = (xwf.Workflow,)
        attrs = {
            'bearer': self,
            'envelope': self.envelope,
            'states': self.states,
            'transitions': self.transitions,
            'initial_state': self.initial_state,
            'log_transition': log_transition
        }

        return type(self.xwf_cls_name, bases, attrs)

    # Resist the temptation to cache this - it will noop the XWF transitions
    @property
    def xwf_methods(self):
        """
        Builds an 'attrs'-style dict of transition & hook methods.

        XWorkflows methods are identified based on the effects of their decorators:
        - @transition wraps methods in a TransisionWrapper
        - hook decorators (@before|after_transition, @on_enter|leave_state)
          set a `xworkflows_hook` attribute on the method
        """
        cls = self.__class__
        return {
            fname: getattr(cls, fname)
            for fname in dir(cls)
            if callable(getattr(cls, fname)) and
               (
                   isinstance(getattr(cls, fname), xwf.base.TransitionWrapper) or
                   hasattr(getattr(cls, fname), 'xworkflows_hook')
               )
        }

    @cached_property
    def xwf_enabled_cls_name(self):
        """Builds a cleaned-up name for the inner XWorkflow-enabled class"""
        pattern = re.compile('[\W_]+')
        return f'XWFEnabled_{re.sub(pattern, "", self.name.capitalize())}'

    @property
    def xwf(self):
        """
        Builds a workflow-enabled class and returns an instance set to the current state.
        """

        def post_transition(self, *args, **kwargs):
            """After transition hook applied to all workflows"""
            info(f'Persisting state change to "{self.state.name}".')
            # Persist state
            self.bearer.previous_state = self.bearer.current_state
            self.bearer.current_state = self.state.name
            self.bearer.save()
            # Mark envelope as finazized when workflow is done
            if self.bearer.finished:
                self.bearer.envelope.finalized = True
                self.bearer.envelope.save()
                info(f'Envelope "{self.bearer.envelope.name}" has been finalized.')
            elif self.bearer.envelope.finalized:
                self.bearer.envelope.finalized = False
                self.bearer.envelope.save()
                info(f'Envelope "{self.bearer.envelope.name}" is no longer finalized.')

        # Transplant the transition methods
        attrs = self.xwf_methods
        attrs.update(
            {
                'state': self.xwf_cls(),
                'bearer': self,
                'post_transition': xwf.after_transition()(post_transition),
                # XWorkflows needs __module__ set on the enabled class
                '__module__': __name__
            }
        )
        cls = type(
            self.xwf_enabled_cls_name,
            (xwf.WorkflowEnabled,),
            attrs)
        wf = cls()
        wf.state = self.current_state  # Force to current state
        return wf

    def start_transition(self, name):
        """Starts a transition on the inner XWorkflow"""
        wf = self.xwf
        if name not in [t.name for t in wf.state.workflow.transitions]:
            raise self.TransitionDoesNotExist('Invalid transition name')

        if name not in [t.name for t in wf.state.transitions()]:
            raise self.TransitionNotAvailable('Transition not allowed from current state')

        getattr(wf, name)()

    def _add_nodes(self, graph):
        """
        Adds workflow states as graph nodes.
        The current state's node will have the `is_current` attribute set.

        Args:
            graph : A `pygraphviz.AGraph` instance.
        Returns:
            The graph with the nodes added.
        """
        for state in self.states:
            if state[0] == self.current_state:
                graph.add_node(state[0], label=state[1], is_current=True)
            else:
                graph.add_node(state[0], label=state[1])
        return graph

    def _add_edges(self, graph):
        """
        Adds workflow transitions as graph edges.

        Args:
            graph : A `pygraphviz.AGraph` instance.
        Returns:
            The graph with the edges added.
        """
        for transition in self.transitions:
            name, src, tgt = transition
            # XWorkflows transitions can have multiple source states
            if isinstance(src, tuple):
                for s in src:
                    graph.add_edge(s, tgt, label=name)
            else:
                graph.add_edge(src, tgt, label=name)
        return graph

    def to_digraph(self, horizontal=True):
        """
        Represents the workflow as a directed graph.

        Returns:
            A `pygraphviz.AGraph` instance.
        """
        graph = self._add_edges(
            self._add_nodes(
                gv.AGraph({}, directed=True)
            )
        )
        if horizontal:
            graph.graph_attr['rankdir'] = 'LR'

        return graph

    def to_json_graph(self):
        """
        Represents the workflow as a dictionary conformant to JSON graph.
        (https://github.com/jsongraph/json-graph-specification)
        """
        nodes = []
        for _state in self.states:
            state, title = _state
            node = {
                'id': state,
                'label': title,
                'metadata': {
                    'initial': state == self.initial_state,
                    'final': state == self.final_state,
                    'current': state == self.current_state
                }
            }
            nodes.append(node)

        edges = []
        for transition in self.transitions:
            name, src, tgt = transition
            # XWorkflows transitions can have multiple source states
            if isinstance(src, tuple):
                for _src in src:
                    edges.append({
                        'id': name,
                        'label': name,
                        'source': _src,
                        'target': tgt
                    })
            else:
                edges.append({
                    'id': name,
                    'label': name,
                    'source': src,
                    'target': tgt
                })

        return {
            'graph': {
                'directed': True,
                'nodes': nodes,
                'edges': edges
            }
        }
