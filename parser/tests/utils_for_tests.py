from ..stateMachine import Literalizer, State
from ..util import StringDict, Gen

from typing import List, Tuple, Final, Callable

text: Final[Callable[[str], State]] = Literalizer("text")
unrelated: Final[Callable[[str], State]] = Literalizer("unrelated")
t1: Final[Callable[[str], State]] = Literalizer("t1")
t2: Final[Callable[[str], State]] = Literalizer("t2")
t3: Final[Callable[[str], State]] = Literalizer("t3")

def checkNumOutputs(outputs: List[StringDict], expectedNum: int) -> None:
    """ Check the number of outputs produced by State.generate(). """
    assert len(outputs) == expectedNum, f"Should have {expectedNum} result(s)."

def checkHasOutput(outputs: List[StringDict], tier: str, target: str) -> None:
    """
    Check that the outputs of State.generate() contain the specified target text
    on the specified tier tier.
    """
    results: Gen[str] = (o[tier] for o in outputs if tier in o)
    # results: Gen[str] = map(lambda o: o[tier], filter(lambda o: tier in o, outputs))
    assert target in results, f"Should have '{target}' on tier '{tier}'."

def checkDoesntHaveOutput(outputs: List[StringDict], tier: str, target: str) -> None:
    """
    Check that the outputs of State.generate() do not contain the specified
    target text on the specified tier tier.
    """
    results: Gen[str] = (o[tier] for o in outputs if tier in o)
    # results: Gen[str] = map(lambda o: o[tier], filter(lambda o: tier in o, outputs))
    assert target not in results, f"Should not have '{target}' on tier '{tier}'."

def checkOutputs(outputs: List[StringDict], expected_outputs: Tuple[StringDict]) -> None:
    """
    Check that the output dictionaries of State.generate() match the expected
    outputs.

    Outputs can be in any order.
    """
    expected_output: StringDict
    for expected_output in expected_outputs:
        assert expected_output in outputs, f"Should have '{expected_output}' in outputs."
    for output in outputs:
        assert output in expected_outputs, f"Should not have '{output}' in outputs."
