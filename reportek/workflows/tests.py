import pytest

from .models import (
    ConfigurationError,
    Context, State,
)


class _State(State):
    def perform(self):
        self.advance()

class InitialState(_State):
    pass

class FinalState(_State):
    pass

class OtherState(_State):
    pass


class TestContextConfiguration():
    def test_missing_transitions(self):
        class Ctx(Context):
            pass
        with pytest.raises(ConfigurationError) as einfo:
            c = Ctx()
        assert str(einfo.value) == 'Must define `Ctx.TRANSITIONS`.'

    def test_missing_initial_state(self):
        class Ctx(Context):
            TRANSITIONS = (
                (InitialState, FinalState),
            )
        with pytest.raises(ConfigurationError) as einfo:
            c = Ctx()
        assert str(einfo.value) == 'Must define an initial state.'

    def test_missing_final_state(self):
        class Ctx(Context):
            TRANSITIONS = (
                (None, InitialState),
                (InitialState, FinalState),
            )
        with pytest.raises(ConfigurationError) as einfo:
            c = Ctx()
        assert str(einfo.value) == 'State `FinalState` is a dead end.'

    def test_simple_configuration_is_ok(self):
        class Ctx(Context):
            TRANSITIONS = (
                (None, InitialState),
                (InitialState, FinalState),
                (FinalState, None),
            )
        c = Ctx()
        assert c

    def test_multiple_exit_paths(self):
        class Ctx(Context):
            TRANSITIONS = (
                (None, InitialState),
                (InitialState, OtherState),
                (InitialState, FinalState),
                (OtherState, FinalState),
                (FinalState, None),
            )
        with pytest.raises(ConfigurationError) as einfo:
            c = Ctx()
        assert str(einfo.value) == 'State `InitialState` has multiple exit paths.'

    def test_configuration_with_conditions_is_ok(self):
        class Ctx(Context):
            TRANSITIONS = (
                (None, InitialState),
                (InitialState, OtherState, lambda state: True),
                (InitialState, FinalState, lambda state: False),
                (OtherState, FinalState),
                (FinalState, None),
            )
        c = Ctx()
        assert c
