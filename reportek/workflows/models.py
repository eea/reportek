class ConfigurationError(RuntimeError):
    pass


class Context():
    TRANSITIONS = ()

    def __init__(self):
        if not self.TRANSITIONS:
            raise ConfigurationError("Must define `%s.TRANSITIONS`."
                                     % self.__class__.__name__)

        transitions = []
        self.__states = {}

        for tdef in self.TRANSITIONS:
            try:
                source, target, condition = tdef
            except ValueError:
                source, target = tdef
                condition = None

            transition = Transition(self._get_state(source),
                                    self._get_state(target),
                                    condition)
            transitions.append(transition)

        self.transitions = tuple(transitions)
        self.states = tuple(self.__states.values())

        self.state = self.get_initial_state()
        self.state.perform()

    def _get_state(self, cls):
        if cls is None:
            return None

        try:
            state = self.__states[cls]
        except KeyError:
            state = cls(context=self)
            self.__states[cls] = state

        return state

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
        raise NotImplementedError(
            "Subclasses of `State` must provide a `perform`()` method.")

    def advance(self):
        self.context.advance()


class Transition():
    def __init__(self, source=None, target=None, condition=None):
        if source is None and target is None:
            raise ConfigurationError(
                "`source` and `target` can't both be undefined."
            )

        self.source = source
        self.target = target
        self.condition = condition

    def check(self):
        # the condition is checked against the source state
        return (
            self.condition is None
            or self.condition(self.source)
        )
