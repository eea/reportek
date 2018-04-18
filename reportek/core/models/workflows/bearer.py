import logging
import xworkflows as xwf
import networkx as nx

from .exceptions import MisconfiguredWorkflowError

log = logging.getLogger('reportek.workflows')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


class XWorkflowBearerMixin:

    # Concrete types MUST set these; see `ReferenceWorkflow`.
    transitions = ()  # WorkflowTransition tuple
    initial_state = None  # The initial WorkflowState
    final_state = None  # The final WorkflowState

    # Override this to indicate the attribute holding the current
    # state on the host class, if different.
    current_state_attr = 'current_state'

    @classmethod
    def collect_states(cls):
        """
        Generates a tuple of the unique `WorkflowState`s used in `transactions`.
        """
        states = set()
        for t in cls.transitions:
            states.update(set(src for src in t.sources))
            states.add(t.target)
        return tuple(states)

    def _get_current_state_cls(self):
        states = self.collect_states()
        for s in states:
            if s.name == getattr(self, self.current_state_attr):
                return s

        return None

    @property
    def current_state_template(self):
        state_cls = self._get_current_state_cls()
        if state_cls is None:
            return None

        return state_cls.template_name

    @classmethod
    def state_names(cls):
        return tuple(s.name for s in cls.collect_states())

    @classmethod
    def transition_names(cls):
        return tuple(t.name for t in cls.transitions)

    @classmethod
    def get_digraph(cls):
        graph = nx.DiGraph()
        for t in cls.transitions:
            for src in t.sources:
                graph.add_edge(src.name, t.target.name)
        return graph

    @classmethod
    def validate_workflow(cls):
        """
        Validates the workflow.

        Checks performed:
         - `initial_state` is in `states`
         - `final_state` is in `states`
         - there is a single possible end state, and it is `final_state`.
        """
        states = cls.collect_states()
        if cls.initial_state not in states:
            raise MisconfiguredWorkflowError(
                f'Invalid workflow configuration: initial state "{cls.initial_state.name}" '
                f'not in `states`: {cls.state_names()}'
            )

        if cls.final_state not in states:
            raise MisconfiguredWorkflowError(
                f'Invalid workflow configuration: final state "{cls.initial_state.name}" '
                f'not in `states`: {cls.state_names()}'
            )

        digraph = cls.get_digraph()
        expected_end_state = cls.final_state.name
        end_states = list(nx.attracting_components(digraph))
        if end_states != [{expected_end_state}]:
            raise MisconfiguredWorkflowError(
                f'Invalid workflow configuration: end state(s) = {end_states} '
                f'but only "{expected_end_state}" is allowed.'
            )

    @classmethod
    def _get_xwf_states(cls):
        """Prepares the state tuple definitions as used by XWorrkflow."""
        return tuple((s.name, s.title) for s in cls.collect_states())

    @classmethod
    def _get_xwf_transitions(cls):
        """Prepares the transition tuple definitions as used by XWorrkflow."""
        return tuple(
            (t.name, tuple(s.name for s in t.sources), t.target.name)
            for t in cls.transitions
        )

    @classmethod
    def get_transition_logger(cls):
        return None

    def xwf_cls(self):
        """
        Builds a custom XWorkflow class from the concrete type's specs.
        """

        self.validate_workflow()

        bases = (xwf.Workflow,)
        attrs = {
            'states': self._get_xwf_states(),
            'transitions': self._get_xwf_transitions(),
            'initial_state': self.initial_state.name,
            'bearer': self,
        }

        logger = self.get_transition_logger()
        if logger is not None:
            attrs['log_transition'] = logger

        return type(f'XWFDef{self.__class__.__name__}', bases, attrs)

    @classmethod
    def _collect_xwf_transition_methods(cls):
        """
        Gathers transition implementations from `WorkflowTransition` instances
        in `transitions`, and applies `TransisionWrapper` on them.

        Returns:
            dict of transition names and implementations.
        """
        implementations = {
            t.name: xwf.transition(t.name)(t.implementation)
            for t in cls.transitions
            if callable(t.implementation)
        }
        # debug(f'{len(implementations.keys())} transitions collected')
        return implementations

    @classmethod
    def _collect_xwf_hook_methods(cls):
        """
        Gathers `on_enter` hook implementations from `WorkflowTransition` instances
        in `transitions`, and applies the `on_enter_state` wrapper on them.

        Returns:
             dict of hook names and implementations.
        """
        hook_methods = {}
        for t in cls.transitions:
            if not callable(t.on_enter_target):
                continue

            # Delete the dict attribute XWorkflows sets on hook methods, if present.
            # Otherwise, each hook collection when building the dynamic XWFEnabled class
            # will add it again to this register-like attribute, leading to multiple hook
            # execution!
            try:
                delattr(t.on_enter_target, 'xworkflows_hook')
            except AttributeError:
                pass

            hook_methods[f'hook_on_enter_state_{t.target.name}'] =  \
                xwf.on_enter_state(t.target.name)(t.on_enter_target)

        # debug(f'{len(hook_methods.keys())} hooks collected')
        return hook_methods

    @classmethod
    def _collect_xwf_concrete_methods(cls):
        """
        Gets the transition and hook methods from the concrete workflow class.

        XWorkflows methods are identified based on the effects of their decorators:
        - @transition wraps methods in a TransisionWrapper
        - hook decorators (@before|after_transition, @on_enter|leave_state)
          set a `xworkflows_hook` attribute on the method
        """

        implementations = {
            fname: getattr(cls, fname)
            for fname in dir(cls)
            if callable(getattr(cls, fname))
            and (
                isinstance(getattr(cls, fname), xwf.base.TransitionWrapper)
                or hasattr(getattr(cls, fname), 'xworkflows_hook')
            )
        }
        # debug(f'{len(implementations.keys())} concrete methods collected')
        return implementations

    @classmethod
    def _collect_xwf_methods(cls):
        """
        Builds an 'attrs'-style dict of transition & hook methods.
        """
        methods = {}
        methods.update(cls._collect_xwf_transition_methods())
        methods.update(cls._collect_xwf_hook_methods())
        methods.update(cls._collect_xwf_concrete_methods())
        # debug(f'{len(methods.keys())} TOTAL methods collected')
        return methods

    @property
    def xwf(self):
        """
        Builds a workflow-enabled class and returns an instance set to the current state.
        """

        wf_cls = self.xwf_cls()
        # Transplant the transition methods
        attrs = self._collect_xwf_methods()
        attrs.update(
            {
                'state': wf_cls(),
                'bearer': self,
                # XWorkflows needs __module__ set on the enabled class
                '__module__': __name__
            }
        )
        klass = type(f'XWFEnabled{self.__class__.__name__}', (xwf.WorkflowEnabled,), attrs)
        wf = klass()
        wf.state = getattr(self, self.current_state_attr)  # Force to current state
        return wf

    def inspect_xwf_hooks(self, transition):
        """
        Returns the hooks available on the XWorkflow instance for `transition`.
        """
        return self.xwf._xworkflows_implems['state'].implementations[transition].hooks
