import pytest

from ..stateMachine import State, Seq, Uni
from ..util import StringDict
from .utils_for_tests import text, t1, t2, checkNumOutputs, checkOutputs

from typing import List, Tuple


# def test_01_literal_text_hello() -> None:
#     grammar: State = text("hello")
#     outputs: List[StringDict] = list(grammar.generate())
#     checkNumOutputs(outputs, 1)
#     checkHasOutput(outputs, "text", "hello")

@pytest.mark.parametrize("grammar, expected_results", [
    # 1. Literal text:hello
    (text("hello"), 
        ({'text': 'hello'},)),
    # 2. Sequence text:hello+text:world
    (Seq(text("hello"), text("world")), 
        ({'text': 'helloworld'},)),
    # 3. Sequence text:hello+text:<empty>
    (Seq(text("hello"), text("")), 
        ({'text': 'hello'},)),
    # 4. Sequence text:<empty>+text:hello
    (Seq(text(""), text("hello")), 
        ({'text': 'hello'},)),

    # 5. Sequence text:hello+text:,+text:world
    (Seq(text("hello"), text(", "), text("world")), 
        ({'text': 'hello, world'},)),
    # 6. Nested sequence (text:hello+text:,)+text:world
    (Seq(Seq(text("hello"), text(", ")), text("world")), 
        ({'text': 'hello, world'},)),
    # 7. Nested sequence text:hello+(text:,+text:world)
    (Seq(text("hello"), Seq(text(", "), text("world"))), 
        ({'text': 'hello, world'},)),
    # 8. Nested sequence text:hello+(text:,)+text:world
    (Seq(text("hello"), Seq(text(", ")), text("world")), 
        ({'text': 'hello, world'},)),

    # 9. Alt text:hello|text:goodbye
    (Uni(text("hello"), text("goodbye")), 
        ({'text': 'hello'}, 
         {'text': 'goodbye'})),
    # 10. Alt of different tiers: t1:hello|t2:goodbye
    (Uni(t1("hello"), t2("goodbye")), 
        ({'t1': 'hello'}, 
         {'t2': 'goodbye'})),

    # 11. Sequence with alt: (text:hello|text:goodbye)+text:world
    (Seq(Uni(text("hello"), text("goodbye")), text("world")), 
        ({'text': 'helloworld'}, 
         {'text': 'goodbyeworld'})),
    # 12. Sequence with alt: text:say+(text:hello|text:goodbye)
    (Seq(text("say"), Uni(text("hello"), text("goodbye"))), 
        ({'text': 'sayhello'}, 
         {'text': 'saygoodbye'})),
    # 13. Sequence with alt: (text:hello|text:goodbye)+(text:world|text:kitty)
    (Seq(Uni(text("hello"), text("goodbye")), Uni(text("world"), text("kitty"))), 
        ({'text': 'helloworld'}, 
         {'text': 'goodbyeworld'}, 
         {'text': 'hellokitty'}, 
         {'text': 'goodbyekitty'})),
])

def test_basics(grammar: State, expected_results: Tuple[StringDict]) -> None:
    outputs: List[StringDict] = list(grammar.generate())
    checkNumOutputs(outputs, len(expected_results))
    checkOutputs(outputs, expected_results)

