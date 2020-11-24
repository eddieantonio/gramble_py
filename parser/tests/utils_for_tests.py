from ..stateMachine import Literalizer, State
from ..util import StringDict, Gen

from typing import List, Final, Callable

text: Final[Callable[[str], State]] = Literalizer("text")
t1: Final[Callable[[str], State]] = Literalizer("t1")
t2: Final[Callable[[str], State]] = Literalizer("t2")
t3: Final[Callable[[str], State]] = Literalizer("t3")

def checkNumOutputs(outputs: List[StringDict], expectedNum: int) -> None:
    assert len(outputs) == expectedNum, f"Should have {expectedNum} result(s)."

def checkHasOutput(outputs: List[StringDict], tier: str, target: str) -> None:
    results: Gen[str] = (o[tier] for o in outputs if tier in o)
    # results: Gen[str] = map(lambda o: o[tier], filter(lambda o: tier in o, outputs))
    assert target in results, f"Should have '{target}' on tier '{tier}'."

def checkDoesntHaveOutput(outputs: List[StringDict], tier: str, target: str) -> None:
    results: Gen[str] = (o[tier] for o in outputs if tier in o)
    # results: Gen[str] = map(lambda o: o[tier], filter(lambda o: tier in o, outputs))
    assert target not in results, f"Should not have '{target}' on tier '{tier}'."
