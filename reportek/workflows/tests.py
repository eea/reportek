import pytest

from .models import (
    ConfigurationError,
    Context, State,
)


class NewState(State):
    pass

class FinalState(State):
    pass

class OtherState(State):
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
                (NewState, FinalState),
            )
        with pytest.raises(ConfigurationError) as einfo:
            c = Ctx()
        assert str(einfo.value) == 'Must define an initial state.'

    def test_missing_final_state(self):
        class Ctx(Context):
            TRANSITIONS = (
                (None, NewState),
                (NewState, FinalState),
            )
        with pytest.raises(ConfigurationError) as einfo:
            c = Ctx()
        assert str(einfo.value) == 'State `FinalState` is a dead end.'

    def test_simple_configuration_is_ok(self):
        class Ctx(Context):
            TRANSITIONS = (
                (None, NewState),
                (NewState, FinalState),
                (FinalState, None),
            )
        c = Ctx()
        assert c

    def test_multiple_exit_paths(self):
        class Ctx(Context):
            TRANSITIONS = (
                (None, NewState),
                (NewState, OtherState),
                (NewState, FinalState),
                (OtherState, FinalState),
                (FinalState, None),
            )
        with pytest.raises(ConfigurationError) as einfo:
            c = Ctx()
        assert str(einfo.value) == 'State `NewState` has multiple exit paths.'

    def test_configuration_with_conditions_is_ok(self):
        class Ctx(Context):
            TRANSITIONS = (
                (None, NewState),
                (NewState, OtherState, (lambda state: True, )),
                (NewState, FinalState,  (lambda state: False, )),
                (OtherState, FinalState),
                (FinalState, None),
            )
        c = Ctx()
        assert c
