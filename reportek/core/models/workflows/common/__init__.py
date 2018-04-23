import enum
import attr

from ....utils import is_proper_sequence


@enum.unique
class WorkflowActors(enum.IntEnum):
    """
    Workflow actors encode the types of entities that can act on a workflow.
    """
    SYSTEM = 0  # Used by automatic transitions
    ADMIN = 1  # Workflow managers, support, etc.
    REPORTER = 2  # Users reporting on an obligation
    CLIENT = 3  # Users acting as client representatives
    AUDITOR = 4  # Users acting as delivery auditors

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)


@attr.s(hash=True)
class WorkflowState:
    """
    Workflow states.
    """
    name = attr.ib(validator=attr.validators.instance_of(str))
    title = attr.ib(validator=attr.validators.instance_of(str))
    template_name = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str))
    )


def is_callable(instance, attribute, value):
    if not callable(value):
        raise TypeError('Expected a callable')


def is_states_seq(instance, attribute, value):
    if not is_proper_sequence(value) or not all(
        isinstance(el, WorkflowState) for el in value
    ):
        raise TypeError('Expected WorkflowState sequence')


def is_actors_list(instance, attribute, value):
    if not is_proper_sequence(value) or not all(
        WorkflowActors.has_value(el) for el in value
    ):
        raise TypeError('Expected WorkflowActors sequence')


@attr.s()
class WorkflowTransition:
    """
    Workflow transitions are defined by:
        - a name - will be set on the implementation method
        - the implementation - a method containing the work to be performed
        - the source states - a list of `WorkflowState`s
        - the target state - a `WorkflowState`
        - the actors allowed to perform the transition - a list of `WorkflowActors`
    """

    name = attr.ib(validator=attr.validators.instance_of(str))
    implementation = attr.ib(validator=is_callable)
    target = attr.ib(validator=attr.validators.instance_of(WorkflowState))
    on_enter_target = attr.ib(
        default=None, validator=attr.validators.optional(validator=is_callable)
    )
    sources = attr.ib(attr.Factory(tuple), validator=is_states_seq)
    allowed_actors = attr.ib(
        default=(WorkflowActors.SYSTEM, WorkflowActors.ADMIN), validator=is_actors_list
    )
