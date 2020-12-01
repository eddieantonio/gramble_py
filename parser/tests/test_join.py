import pytest

from ..stateMachine import State, Seq, Uni, Join
from ..util import StringDict
from .utils_for_tests import text, t1, t2, t3, unrelated, \
                             checkNumOutputs, checkOutputs

from typing import List, Tuple


@pytest.mark.parametrize("grammar, expected_results", [
    # 1. Joining text:hello & text:hello
    (Join(text("hello"), text("hello")), 
        ({'text': 'hello'},)),
     # 2. Joining text:hello & text:hello+text:<emtpy>
    (Join(text("hello"), Seq(text("hello"), text(""))), 
        ({'text': 'hello'},)),
    # 3. Joining text:hello & text:<emtpy>+text:hello
    (Join(text("hello"), Seq(text(""), text("hello"))), 
        ({'text': 'hello'},)),
    # 4. Joining text:<emtpy>+text:hello & text:hello
    (Join(Seq(text(""), text("hello")), text("hello")), 
        ({'text': 'hello'},)),
    # 5. Joining text:hello+text:<emtpy> & text:hello
    (Join(Seq(text("hello"), text("")), text("hello")), 
        ({'text': 'hello'},)),
    # 6. Joining Seq(text:hello) & text:hello
    (Join(Seq(text("hello")), text("hello")), 
        ({'text': 'hello'},)),
    # 7. Joining text:hello & Seq(text:hello)
    (Join(text("hello"), Seq(text("hello"))), 
        ({'text': 'hello'},)),
    # 8. Joining Uni(text:hello) & text:hello
    (Join(Uni(text("hello")), text("hello")), 
        ({'text': 'hello'},)),
    # 9. Joining text:hello & Uni(text:hello
    (Join(text("hello"), Uni(text("hello"))), 
        ({'text': 'hello'},)),

    # 10. Joining t1:hi & t1:hi+t2:bye
    (Join(t1("hi"), Seq(t1("hi"), t2("bye"))), 
        ({'t1': 'hi', 't2': 'bye'},)),
    # 11. Joining (t1:hi & t1:hi+t2:bye) & t2:bye+t3:yo
    (Join(Join(t1("hi"), Seq(t1("hi"), t2("bye"))), Seq(t2("bye"), t3("yo"))), 
         ({'t1': 'hi', 't2': 'bye', 't3': 'yo'},)),
 
    # 12. Joining text:hello+text:world & text:hello+text:world
    (Join(Seq(text("hello"), text("world")), Seq(text("hello"), text("world"))), 
        ({'text': 'helloworld'},)),
    # 13. Joining t1:hello+t1:kitty & t1:hello+t2:goodbye+t1:kitty+t2:world
    (Join(Seq(t1("hello"), t1("kitty")), Seq(t1("hello"), t2("goodbye"), t1("kitty"), t2("world"))), 
        ({'t1': 'hellokitty', 't2': 'goodbyeworld'},)),
    # 14. Joining t1:hello+t1:kitty & (t1:hello+t1:kitty)+(t2:goodbye+t2:world)
    (Join(Seq(t1("hello"), t1("kitty")), Seq(Seq(t1("hello"), t1("kitty")), Seq(t2("goodbye"), t2("world")))), 
        ({'t1': 'hellokitty', 't2': 'goodbyeworld'},)),
    # 15. Joining t1:hello+t1:kitty & (t1:hello+t2:goodbye)+(t1:kitty+t2:world)
    (Join(Seq(t1("hello"), t1("kitty")), Seq(Seq(t1("hello"), t2("goodbye")), Seq(t1("kitty"), t2("world")))), 
        ({'t1': 'hellokitty', 't2': 'goodbyeworld'},)),
    # 16. Joining t1:hello+t1:kitty & (t1:hello+t2:goodbye)+(t2:world+t1:kitty)
    (Join(Seq(t1("hello"), t1("kitty")), Seq(Seq(t1("hello"), t2("goodbye")), Seq(t2("world"), t1("kitty")))), 
        ({'t1': 'hellokitty', 't2': 'goodbyeworld'},)),
    # 17. Joining t1:hello+t1:kitty & (t1:hello+t2:goodbye+t1:kitty)+t2:world
    (Join(Seq(t1("hello"), t1("kitty")), Seq(Seq(t1("hello"), t2("goodbye"), t1("kitty")), t2("world"))), 
        ({'t1': 'hellokitty', 't2': 'goodbyeworld'},)),

    # 18. Joining an alternation & literal
    (Join(Uni(t1("hi"), t1("yo")), Seq(t1("hi"), t2("bye"))), 
        ({'t1': 'hi', 't2': 'bye'},)),
    # 19. Joining t1:hi & (t1:hi+t2:bye & t2:bye+t3:yo)
    (Join(t1("hi"), Join(Seq(t1("hi"), t2("bye")), Seq(t2("bye"), t3("yo")))), 
         ({'t1': 'hi', 't2': 'bye', 't3': 'yo'},)),
    # 20. Joining of (t1:hi & t1:hi+t2:bye)+t2:world
    (Seq(Join(t1("hi"), Seq(t1("hi"), t2("bye"))), t2("world")), 
        ({'t1': 'hi', 't2': 'byeworld'},)),

   # 21. Joining text:hello & text:hello+text:world
    (Join(text("hello"), Seq(text("hello"), text("world"))), 
        ()),
    # 22. Joining text:hello & text:helloworld
    (Join(text("hello"), text("helloworld")), 
        ()),
    # 23. Joining text:hello & text:hello+text:world
    (Join(text("hello"), Seq(text("hello"), text("world"))), 
        ()),
    # 24. Joining text:helloworld & text:hello
    (Join(text("helloworld"), text("hello")), 
        ()),
    # 25. Joining text:hello+text:world & text:hello
    (Join(Seq(text("hello"), text("world")), text("hello")), 
        ()),

    # 26. Joining text:hi+unrelated:world & text:hi+unrelated:world
    (Join(Seq(text("hi"), unrelated("world")), Seq(text("hi"), unrelated("world"))), 
        ({'text': 'hi', 'unrelated': 'world'},)),
    # 27. Joining unrelated:world+text:hello & text:hello+unrelated:world
    (Join(Seq(unrelated("world"), text("hello")), Seq(text("hello"), unrelated("world"))), 
        ({'text': 'hello', 'unrelated': 'world'},)),

    # 28. Joining text:hello & text:hello+unrelated:foo
    (Join(text("hello"), Seq(text("hello"), unrelated("foo"))), 
        ({'text': 'hello', 'unrelated': 'foo'},)),
    # 29. Joining text:hello & unrelated:foo+text:hello
    (Join(text("hello"), Seq(unrelated("foo"),text("hello"))), 
        ({'text': 'hello', 'unrelated': 'foo'},)),
    # 30. Joining text:hello+unrelated:foo & text:hello
    (Join(Seq(text("hello"), unrelated("foo")), text("hello")), 
        ({'text': 'hello', 'unrelated': 'foo'},)),
    # 31. Joining unrelated:foo+text:hello & text:hello
    (Join(Seq(unrelated("foo"), text("hello")), text("hello")), 
        ({'text': 'hello', 'unrelated': 'foo'},)),

    # 32. Joining text:hello+unrelated:foo & text:hello+unrelated:bar
    (Join(Seq(text("hello"), unrelated("foo")), Seq(text("hello"), unrelated("bar"))), 
        ()),
    # 33. Joining (text:hello|text:goodbye) & (text:goodbye|text:welcome)
    (Join(Uni(text("hello"), text("goodbye")), Uni(text("goodbye"), text("welcome"))), 
        ({'text': 'goodbye'},)),
    # 34. Joining (text:goodbye|text:welcome) & (text:hello|text:goodbye)
    (Join(Uni(text("goodbye"),  text("welcome")), Uni(text("hello"), text("goodbye"))), 
        ({'text': 'goodbye'},)),
    # 35. Nested joining, leftward
    (Join(Join(Uni(text("hello"), text("goodbye")), Uni(text("goodbye"), text("welcome"))), Uni(text("yo"), text("goodbye"))), 
        ({'text': 'goodbye'},)),
    # 36. Nested joining, rightward
    (Join(Uni(text("yo"), text("goodbye")), Join(Uni(text("hello"), text("goodbye")), Uni(text("goodbye"),  text("welcome")))), 
        ({'text': 'goodbye'},)),

    # 37. Joining to joining text:hello & text:hello
    (Join(text("hello"), Join(text("hello"), text("hello"))), 
        ({'text': 'hello'},)),
    # 38. Joining to joining of (text:hello|text:goodbye) & (text:goodbye|text:welcome)
    (Join(text("goodbye"), Join(Uni(text("hello"), text("goodbye")), Uni(text("goodbye"),  text("welcome")))), 
        ({'text': 'goodbye'},)),
    # 39. Joining to joining of (text:goodbye|text:welcome) & (text:hello|text:goodbye)
    (Join(text("goodbye"), Join(Uni(text("goodbye"), text("welcome")), Uni(text("hello"), text("goodbye")))), 
        ({'text': 'goodbye'},)),
    # 40. Joining to nested joining, leftward
    (Join(text("goodbye"), Join(Join(Uni(text("hello"), text("goodbye")), Uni(text("goodbye"), text("welcome"))), Uni(text("yo"), text("goodbye")))), 
        ({'text': 'goodbye'},)),
    # 41. Joining to nested joining, rightward
    (Join(text("goodbye"), Join(Uni(text("yo"), text("goodbye")), Join(Uni(text("hello"), text("goodbye")), Uni(text("goodbye"),  text("welcome"))))), 
        ({'text': 'goodbye'},)),

    # 42. Joining to a sequence of alternating sequences
    (Join(text("hello"), Seq(Uni(Seq(text("hello"), unrelated("hola")), Seq(text("goodbye"), unrelated("adios"))))), 
        ({'text': 'hello', 'unrelated': 'hola'},)),
    # 43. Joining to a sequence of alternating sequences
    (Join(Seq(text("hello"), unrelated("adios")), Seq(Uni(Seq(text("hello"),unrelated("hola")), Seq(text("goodbye"), unrelated("adios"))))), 
        ()),
   # 44. Joining to an alt of different tiers
    (Join(text("hello"), Uni(text("hello"), unrelated("foo"))), 
        ({'text': 'hello'},
         {'text': 'hello', 'unrelated': 'foo'})),

    # 45. Joining unrelated-tier alts in same direction
    (Join(Uni(text("hello"), unrelated("foo")), Uni(text("hello"), unrelated("foo"))), 
        ({'text': 'hello'},
         {'unrelated': 'foo'},
         {'text': 'hello', 'unrelated': 'foo'},
         {'text': 'hello', 'unrelated': 'foo'})),
    # 46. Joining unrelated-tier alts in different directions
    (Join(Uni(unrelated("foo"), text("hello")), Uni(text("hello"), unrelated("foo"))), 
        ({'unrelated':"foo"}, 
         {'text':"hello"},
         {'text':"hello", 'unrelated':"foo"},
         {'text':"hello", 'unrelated':"foo"})),
    # 47. Joining unrelated-tier alts in different directions
    (Join(Uni(text("hello"), unrelated("foo")), Uni(unrelated("foo"), text("hello"))), 
        ({'unrelated':"foo"}, 
         {'text':"hello"},
         {'text':"hello", 'unrelated':"foo"},
         {'text':"hello", 'unrelated':"foo"})),
])

def test_join(grammar: State, expected_results: Tuple[StringDict]) -> None:
    outputs: List[StringDict] = list(grammar.generate())
    checkNumOutputs(outputs, len(expected_results))
    checkOutputs(outputs, expected_results)
