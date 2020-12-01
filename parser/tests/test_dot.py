import pytest

from ..stateMachine import State, Seq, Join, Any
from ..util import StringDict
from .utils_for_tests import text, checkNumOutputs, checkOutputs

from typing import List, Tuple


@pytest.mark.parametrize("grammar, expected_results", [
# Tests with the dot on the right side 
    # 1. Joining text:h & text:.
    (Join(text("h"), Any("text")), 
        ({'text': 'h'},)),
    # 2. Joining text:hello & text:.ello
    (Join(text("hello"), Seq(Any("text"), text('ello'))), 
        ({'text': 'hello'},)),
    # 3. Joining text:ello & text:.ello
    (Join(text("ello"), Seq(Any("text"), text('ello'))), 
        ()),
    # 4. Joining text:hello & text:h.llo
    (Join(text("hello"), Seq(text("h"), Any("text"), text('llo'))), 
        ({'text': 'hello'},)),
    # 5. Joining text:hllo & text:h.llo
    (Join(text("hllo"), Seq(text("h"), Any("text"), text('llo'))), 
        ()),
    # 6. Joining text:hello & text:hell.
    (Join(text("hello"), Seq(text("hell"), Any("text"))), 
        ({'text': 'hello'},)),
    # 7. Joining text:hell & text:hell.
    (Join(text("hell"), Seq(text("hell"), Any("text"))), 
        ()),
# The same tests but with the dot on the left side
    # 8. Joining text:. & text:h
    (Join(Any("text"), text("h")), 
        ({'text': 'h'},)),
    # 9. Joining text:.ello & text:hello
    (Join(Seq(Any("text"), text('ello')), text("hello")), 
        ({'text': 'hello'},)),
    # 10. Joining text:.ello & text:ello
    (Join(Seq(Any("text"), text('ello')), text("ello")), 
        ()),
    # 11. Joining text:h.llo & text:hello
    (Join(Seq(text("h"), Any("text"), text('llo')), text("hello")), 
        ({'text': 'hello'},)),
    # 12. Joining text:h.llo & text:hllo
    (Join(Seq(text("h"), Any("text"), text('llo')), text("hllo")), 
        ()),
    # 13. Joining text:hell. & text:hello
    (Join(Seq(text("hell"), Any("text")), text("hello")), 
        ({'text': 'hello'},)),
    # 14. Joining text:hell. & text:hell
    (Join(Seq(text("hell"), Any("text")), text("hell")), 
        ()),
])

def test_dot(grammar: State, expected_results: Tuple[StringDict]) -> None:
    outputs: List[StringDict] = list(grammar.generate())
    checkNumOutputs(outputs, len(expected_results))
    checkOutputs(outputs, expected_results)
