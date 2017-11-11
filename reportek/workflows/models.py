class ConfigurationError(RuntimeError):
    pass


class Context():
    TRANSITIONS = ()

    def __init__(self):
        if not self.TRANSITIONS:
            raise ConfigurationError("Must define `%s.TRANSITIONS`."
                                     % self.__class__.__name__)

        transitions = []
        states = {}

        def _get_state(cls):
            if cls is None:
                return None

            try:
                state = states[cls]
            except KeyError:
                state = cls(context=self)
                states[cls] = state

            return state

        for tdef in self.TRANSITIONS:
            try:
                source, target, conditions = tdef
            except ValueError:
                source, target = tdef
                conditions = None

            transition = Transition(_get_state(source),
                                    _get_state(target),
                                    conditions)
            transitions.append(transition)

        self.transitions = tuple(transitions)
        self.states = tuple(states.values())

        self.state = self.get_initial_state()
        self.state.perform()

    def advance(self):
        self.state = self.get_next_state()
        if self.state:
            self.state.perform()

    def get_initial_state(self):
        transitions = [t for t in self.transitions if t.source is None]
        if not transitions:
            raise ConfigurationError("Must define an initial state.")
        if len(transitions) > 1:
            raise ConfigurationError("Multiple initial states found.")

        return transitions[0].target

    def get_next_state(self):
        transitions = [t for t in self.transitions if t.source is self.state]
        if not transitions:
            raise ConfigurationError("State `%s` is a dead end."
                                     % self.state.__class__.__name__)

        transitions = [t for t in transitions if t.check()]
        if len(transitions) > 1:
            raise ConfigurationError("State `%s` has multiple exit paths."
                                     % self.state.__class__.__name__)

        return transitions[0].target


class State():
    def __init__(self, context):
        self.context = context

    def perform(self):
        self.context.advance()


class Transition():
    def __init__(self, source=None, target=None, conditions=None):
        if source is None and target is None:
            raise ConfigurationError(
                "`source` and `target` can't both be undefined."
            )
        if conditions is None:
            conditions = ()
        self.source = source
        self.target = target
        self.conditions = conditions

    def check(self):
        # conditions are checked only against the source state
        return all(
            condition(self.source)
            for condition in self.conditions
        )
