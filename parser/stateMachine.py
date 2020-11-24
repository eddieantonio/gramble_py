from __future__ import annotations

from .util import StringDict, Gen, BitSet
from .tapes import MultiTapeOutput, Tape, StringTape, RenamedTape, \
                  TapeCollection, Token, ANY_CHAR, NO_CHAR

from typing import Final, Optional, List, Dict, Tuple, Callable
from abc import ABC, abstractmethod

import sys
import json

"""
This is the parsing engine that underlies Gramble.
It executes a multi-tape recursive state machine.

     - "Multi-tape" means that there are multiple "tapes"
     (in the Turing machine sense) from/to which the machine
     can read/write.  Finite-state acceptors are one-tape automata,
     they read in from one tape and either succeed or fail.  Finite-
     state transducers are two-tape automata, reading from one and
     writing to another.  This system allows any number of tapes.

     - "Recursive" means that states can themselves contain states,
     meaning that the machine can parse context-free languages rather
     than just regular languages.  (Recursive and push-down automata
     are equivalent, but I hesitate to call this "push-down" because 
     states/transitions don't perform any operations to the stack.)
     
The execution of this particular state machine is lazy, 
in the sense that we don't necessarily construct the entire machine.
Each state constructs successor states as necessary.
"""


class CounterStack:
    """ CounterStack
    
    A convenience class that works roughly like Python's collections.Counter.
    Just note that add() is non-destructive; it returns a new Counter without
    changing the original.
    So use it like:
        counter = counter.add("verb")
    
    We use this to make sure we don't recurse an impractical number of times,
    like infinitely.  
    
    Infinite recursion is *correct* behavior for a grammar that's genuinely
    infinite, but because this system is meant to be embedded in a programming
    language meant for beginner programmers, we default to allowing four
    recursions before stopping recursion.  Advanced programmers will be able to
    turn this off and allow infinite recursion, but they have to take an extra
    step to do so.
    """
    def __init__(self, max: int = 4) -> None:
        self.max: int = max
        self.stack: Dict[str, int] = {}

    def add(self, key: str) -> CounterStack:
        result: CounterStack = CounterStack(self.max)
        result.stack[key] = 0
        result.stack.update(self.stack)
        result.stack[key] += 1
        return result
    
    def get(self, key: str) -> int:
        return self.stack.get(key, 0)

    def exceedsMax(self, key: str) -> bool:
        return self.get(key) >= self.max

    def toString(self) -> str:
        return json.dumps(self.stack)


class StateError(Exception):
    """ Exception raised for state machine errors.

    Attributes:
        msg: explanatory error message 
    """
 
    def __init__(self, msg: str) -> None:
        self.msg = msg


class State(ABC):
    """ State Abstract Base Class

    State is the basic class of the parser.  It encapsulate the current state of
    the parse; you can think of it like a pointer into the state graph, if we
    were to ever construct that graph, which we don't. Rather, a State
    encapsulates the *information* that that node would have represented.  

    For example, imagine an automaton that recognizes the literal "hello".  We
    could implement this as an explicit graph of nodes, where each node leads to
    the next by consuming a particular letter (state 0 leads to 1 by consuming
    "h", state 1 leads to 2 by consuming "e", etc.).  Our pointer into this
    graph basically represents two pieces of information, what the word is
    ("hello") and how far into it we are.  We could also represent this
    information as an object { text: string, index: number }. Rather than
    pre-compute each of these nodes, we can say that this object returns (upon
    matching) another object {text: string, index: number+1}... until we exceed
    the length of the literal, of course.  This idea, in general, allows us to
    avoid creating explicit state graphs that can be exponentially huge,
    although it comes with its own pitfalls.

    For our purposes, a State is anything that can, upon being queried with a
    [tape, char] pair, return the possible successor states it can get to.  

    Many kinds of States have to contain references to other states (like an
    [EmbedState], which lets us embed grammars inside other grammars, keeps a
    point to the current parse state inside that embedded grammar).  The
    structure of State components ends up being roughly isomorphic to the
    grammar that it's parsing (e.g. if the grammar is (A+(B|C)), then the start
    State that we begin in will have the same structure, it'll be a
    [ConcatState] of (A and a [UnionState] of (B and C)).  Then as the parse
    goes on, the State will simplify bit-by-bit, like once A is recognized, the
    current state will just be one corresponding to B|C, and if B fails, the
    current state will just be C.

    For the purposes of the algorithm, there are three crucial functions of States:

        ndQuery(tape, char): What states can this state get to, compatible with
            a given tape/character.
        dQuery(tape, char): Calls ndQuery and rearranges the outputs so that any
            specific character can only lead to one state.
        accepting(): Whether this state is a final state, meaning it consistutes
            a complete parse.
    """
    @property
    @abstractmethod
    def id(self) -> str:
        """
        Return an ID for the state.  At the moment we're only using this for
        debugging purposes, but we may want to use it in the future as a unique
        identifier for a state in explicit graph construction.

        If we do this, we should go through and make sure that IDs are actually
        unique; right now they're often not.
        """
        pass

    def accepting(self, symbolStack: CounterStack) -> bool:
        """
        Return whether the state is accepting (i.e. indicates that we have
        achieved a complete parse).  (What is typically rendered as a "double
        circle" in a state machine.) Note that, since this is a recursive state
        machine, getting to an accepting state doesn't necessarily mean that the
        *entire* grammar has completed; we might just be in a subgrammar.  In
        this case, accepting() isn't the signal that we can stop parsing, just
        that we've reached a complete parse within the subgrammar.  For example,
        [ConcatState] checks whether its left child is accepting() to determine
        whether to move on and start parsing its right child.
        """
        return False

    @abstractmethod
    def ndQuery(self,
                tape: Tape, 
                target: Token, 
                symbolStack: CounterStack) -> Gen[Tuple[Tape, Token, bool, State]]:
        """
        non-deterministic Query
        
        The workhorse function of the parser, taking a <tape, char> pair and
        trying to match it to a transition (e.g., matching it to the next
        character of a [LiteralState]).  It yields all matching <tape, char>
        pairs, and the respective nextStates to which we should move upon a
        successful transition.

        Note that an ndQuery's results may "overlap" in the sense that you may
        get the same matched character twice (e.g., you might get two results
        "q", or a result "q" and a result "__ANY__" that includes "q"). For some
        parts of the algorithm, this would be inappropriate (i.e., inside of a
        negation).  So rather than call ndQuery directly, call dQuery
        (deterministic Query), which calls ndQuery and then adjusts the results
        so that the results are disjoint.
        
        @param tape A Tape object identifying the name/type/vocabulary of the
                    relevant tape
        @param target A Token identifying what characters we need to match
        @param symbolStack A [CounterStack] that keeps track of symbols (for
                    embedding grammars), used for preventing infinite recursion
        @returns A 4-tuple (tape, match, matched, nextState), where:
            tape is the tape we matched on, 
            match is the intersection of the original target and our match,
            matched is whether we actually made a match or ignored it (for being
                on the wrong tape)
            nextState is the state the matched transition leads to.
        """
        pass

    def dQuery(self,
               tape: Tape, 
               target: Token, 
               symbolStack: CounterStack) -> Gen[Tuple[Tape, Token, bool, State]]:
        """ deterministic Query
        
        Query the state so that the results are deterministic (or more
        accurately, so that all returned transitions are disjoint).  (There can
        still be multiple results; when we query ANY:ANY, for example.)

        This looks a bit complicated (and it kind of is) but what it's doing is
        handing off the query to ndQuery, then combining results so that there's
        no overlap between the tokens.  For example, say ndQuery yields two
        tokens X and Y, and they have no intersection.  Then we're good, we just
        yield those.  But if they do have an intersection, we need to return
        three paths:
        
           X&Y (leading to the UnionState of the states X and Y would have led to)
           X-Y (leading to the state X would have led to)
           Y-X (leading to the state Y would have led to)
        
        @param tape A Tape object identifying the name/type/vocabulary of the
                    relevant tape
        @param target A Token identifying what characters we need to match
        @param symbolStack A [CounterStack] that keeps track of symbols (for
                    embedding grammars), used for preventing infinite recursion
        @returns A 4-tuple (tape, match, matched, nextState), where:
            tape is the tape we matched on, 
            match is the intersection of the original target and our match,
            matched is whether we actually made a match or ignored it (for being
                on the wrong tape)
            nextState is the state the matched transition leads to.
        """
        results: List[Tuple[Tape, Token, bool, State]] = []
        nextStates: List[Tuple[Tape, Token, bool, State]] 
        nextStates = list(self.ndQuery(tape, target, symbolStack))
        for tape, bits, matched, nxt in nextStates:
            if tape.numTapes == 0:
                results.append((tape, bits, matched, nxt))
                continue

            newResults: List[Tuple[Tape, Token, bool, State]] = []
            for otherTape, otherBits, otherMatched, otherNext in results:
                if (tape.tapeName != otherTape.tapeName):
                    newResults.append((otherTape, otherBits, otherMatched, otherNext))
                    continue

                intersection: Token = bits.and_(otherBits)
                if not intersection.isEmpty():
                    union: State = UnionState(nxt, otherNext)
                    newResults.append((tape, intersection, matched or otherMatched, union))
                bits = bits.andNot(intersection)
                otherBits = otherBits.andNot(intersection)
                if not otherBits.isEmpty():
                    newResults.append((otherTape, otherBits, otherMatched, otherNext))
            results = newResults
            if not bits.isEmpty():
                results.append((tape, bits, matched, nxt))
        yield from results

    def generate(self, maxRecursion: int = 4, maxChars: int = 1000) -> Gen[StringDict]:
        """
        Perform a breadth-first traversal of the graph.  This will be the
        function that most clients will be calling.

        Note that there's no corresponding "parse" function, only "generate".
        To do parses, we join the grammar with a grammar corresponding to the
        query.  E.g., if we wanted to parse { text: "foo" } in grammar X, we
        would construct JoinState(LiteralState("text", "foo"), X). The reason
        for this is that it allows us a diverse collection of query types for
        free, by choosing an appropriate "query grammar" to join X with.
        
        @param [maxRecursion] The maximum number of times the grammar can
                    recurse; for infinite recursion pass Infinity.
        @param [maxChars] The maximum number of steps any one traversal can take
                    (roughly == the total number of characters output to all
                    tapes)
        @returns a generator of { tape: string } dictionaries, one for each
            successful traversal. 
        """
        allTapes: TapeCollection = TapeCollection()
        self.collectVocab(allTapes, [])
        initialOutput: MultiTapeOutput = MultiTapeOutput()
        stateQueue: List[Tuple[MultiTapeOutput, State]] = [(initialOutput, self)]
        symbolStack = CounterStack(maxRecursion)
        chars: int = 0

        while len(stateQueue) > 0 and chars < maxChars:
            nextQueue: List[Tuple[MultiTapeOutput, State]] = []
            for prevOutput, prevState in stateQueue:
                if prevState.accepting(symbolStack):
                    yield from prevOutput.toStrings()
                for tape, c, matched, newState in prevState.dQuery(allTapes, ANY_CHAR, symbolStack):
                    if not matched:
                        print("Warning: got all the way through without a match", file=sys.stderr)
                        continue
                    nextOutput: MultiTapeOutput = prevOutput.add(tape, c)
                    nextQueue.append((nextOutput, newState))
            stateQueue = nextQueue
            chars += 1
    
    def collectVocab(self, tapes: Tape, stateStack: List[str]) -> None:
        """
        Collect all explicitly mentioned characters in the grammar for all tapes.
        
        @param tapes A TapeCollection for holding found characters
        @param stateStack What symbols we've already collected from, to prevent
                    inappropriate recursion
        @returns vocab
        """
        pass


class TextState(State):
    """ Text State

    Abstract base class for both LiteralState and AnyCharState, since they share
    the same query algorithm template.

    In order to implement TextState, a descendant class must implement
    _firstToken() (giving the first token that needs to be matched) and
    _successor() (returning the state to which we would transfer upon successful
    matching of the token).

    There is a inherent assumption that collectVocab is called before
    _firstToken() is ever called.
    """
    def __init__(self, tapeName: str) -> None:
        self.tapeName = tapeName
        super().__init__()

    @abstractmethod
    def _firstToken(self, tape: Tape) -> Token:
        pass

    @abstractmethod
    def _successor(self) -> State:
        pass

    def ndQuery(self,
                tape: Tape, 
                target: Token, 
                symbolStack: CounterStack) -> Gen[Tuple[Tape, Token, bool, State]]:

        matchedTape: Optional[Tape] = tape.matchTape(self.tapeName)
        if matchedTape is None:
            yield (tape, target, False, self)
            return
        
        if self.accepting(symbolStack):
            return

        bits: Token = self._firstToken(matchedTape)
        result: Token = matchedTape.match(bits, target)
        nextState: State = self._successor()
        yield (matchedTape, result, True, nextState)


class AnyCharState(TextState):
    """ Any Character State

    The state that recognizes/emits any character on a specific tape; 
    implements the "dot" in regular expressions.
    """
    @property
    def id(self) -> str:
        return f"{self.tapeName}:(ANY)"

    def _firstToken(self, tape: Tape) -> Token:
        return tape.any()
    
    def _successor(self) -> State:
        return TrivialState()


class LiteralState(TextState):
    """ Literal State

    Recognizese/emits a literal string on a particular tape.  Inside, it's just
    a string like "foo"; upon successfully matching "f" we construct a successor
    state looking for "oo", and so on.
    
    The first time we construct a LiteralState, we just pass in the text
    argument, and leave tokens empty.  (This is because, at the initial point of
    construction of a LiteralState, we don't know what the total character
    vocabulary of the grammar is yet, and thus can't tokenize it into Tokens
    yet.)  On subsequent constructions, like in successor(), we've already
    tokenized, so we pass the remainder of the tokens into the tokens argument.
    It doesn't really matter what we pass into text in subsequent constructions,
    it's not used except for debugging. In the TypeScript implementation, we
    just pass in the original text, but in this implementation we pass in the
    remainder of the text after removing the string associated with the previous
    token.
    """
    def __init__(self, tapeName: str, text: str, 
                 tokens: List[Token] = [], tapes: Optional[Tape] = None) -> None:
        self.text = text
        self._tokens = tokens
        self._tapes = tapes
        super().__init__(tapeName)

    @property
    def id(self) -> str:
        return f"{self.tapeName}:{self.text}"

    def accepting(self, symbolStack: CounterStack) -> bool:
        return len(self._tokens) == 0

    def collectVocab(self, tapes: Tape, stateStack: List[str]) -> None:
        self._tokens = tapes.tokenize(self.tapeName, self.text)
        self._tapes = tapes

    def _firstToken(self, tape: Tape) -> Token:
        return self._tokens[0]
    
    def _successor(self) -> State:
        newTokens: List[Token] = self._tokens[1:]
        # newText: str = "".join("".join(self._tapes.fromBits(self.tapeName, t.bits))
        #                        for t in newTokens)
        firstText: str = "".join(self._tapes.fromBits(self.tapeName, self._tokens[0].bits))
        newText: str = self.text[len(firstText):]
        return LiteralState(self.tapeName, newText, newTokens, self._tapes)


class TrivialState(State):
    """
    Recognizes the empty grammar.  This is occassionally useful in implementing
    other states (e.g. when you need a state that's accepting but won't go
    anywhere).
    """
    def __init__(self) -> None:
        super().__init__()

    @property
    def id(self) -> str:
        return "0"
    
    def accepting(self, symbolStack: CounterStack) -> bool:
        return True

    def ndQuery(self,
                tape: Tape, 
                target: Token, 
                symbolStack: CounterStack) -> Gen[Tuple[Tape, Token, bool, State]]:
        pass


class BinaryState(State):
    """
    Abstract base class of all States with two state children (e.g. [JoinState],
    [ConcatState], [UnionState]). States that conceptually might have infinite
    children (like Union) we treat as right-recursive binary (see for example
    the helper function [Uni] which converts lists of states into
    right-branching UnionStates).
    """
    def __init__(self, child1: State, child2: State) -> None:
        self.child1 = child1
        self.child2 = child2
        # super.__init__()
    
    def collectVocab(self, tapes: Tape, stateStack: List[str]) -> None:
        self.child1.collectVocab(tapes, stateStack)
        self.child2.collectVocab(tapes, stateStack)

    @property
    def id(self) -> str:
        return f"{self.__class__.__name__}({self.child1.id},{self.child2.id})"

    def accepting(self, symbolStack: CounterStack) -> bool:
        return self.child1.accepting(symbolStack) and self.child2.accepting(symbolStack)


class ConcatState(BinaryState):
    """
    ConcatState represents the current state in a concatenation A+B of two
    grammars.  It is a [BinaryState], meaning it has two children; sequences
    ABCDEF are constructed as A+(B+(C+(D+(E+F)))).

    The one thing that makes ConcatState a bit tricky is that they are the only
    part of the grammar where there is a precedence order, which in a naive
    implementation can lead to a deadlock situation. For example, if we have
    ConcatState(LiteralState("A","a"), LiteralState("B","b")), then the material
    on tape A needs to be emitted/matched before the material on tape B.  But
    then consider the opposite, ConcatState(LiteralState("B","b"),
    LiteralState("A","a")).  That grammar describes the same database, but looks
    for the material in opposite tape order.  If we join these two, the first is
    emitting on A and waiting for a match, but the second can't match it because
    it'll only get there later.  There are several possible solutions for this,
    but the simplest by far is to implement ConcatState so that it can always
    emit/match on any tape that any of its children refer to.  Basically, it
    goes through its children, and if child1 returns but doesn't match (meaning
    it doesn't care about tape T), it asks child2.  Then it returns the
    appropriate ConcatState consisting of the unmatched material.
    """
    def ndQuery(self,
                tape: Tape, 
                target: Token, 
                symbolStack: CounterStack) -> Gen[Tuple[Tape, Token, bool, State]]:
        # We can yield from child2 if child1 is accepting, OR if child1 doesn't
        # care about the requested tape, but if child1 is accepting AND doesn't
        # care about the requested tape, we don't want to yield twice; that
        # leads to duplicate results.  yieldedAlready is how we keep track of
        # that.
        yieldedAlready: bool = False

        for c1tape, c1text, c1matched, c1next in self.child1.dQuery(tape, target, symbolStack):
            if c1matched:
                yield (c1tape, c1text, c1matched, ConcatState(c1next, self.child2))
                continue
            # child1 not interested in the requested tape, the first character
            # on the tape must be (if it exists at all) in child2.
            for c2tape, c2text, c2matched, c2next in self.child2.dQuery(tape, target, symbolStack):
                yield (c2tape, c2text, c2matched, ConcatState(self.child1, c2next))
                yieldedAlready = True

        if not yieldedAlready and self.child1.accepting(symbolStack):
            yield from self.child2.dQuery(tape, target, symbolStack)


class UnionState(BinaryState):
    """
    UnionStates are very simple; they just have a left child and a right child,
    and upon querying they yield from the first and then yield from the second.

    Note that UnionStates are only around initally; they don't construct
    successor UnionStates, their successors are just the successors of their
    children.
    """
    def accepting(self, symbolStack: CounterStack) -> bool:
        return self.child1.accepting(symbolStack) or self.child2.accepting(symbolStack)

    def ndQuery(self,
                tape: Tape, 
                target: Token, 
                symbolStack: CounterStack) -> Gen[Tuple[Tape, Token, bool, State]]:
        yield from self.child1.dQuery(tape, target, symbolStack)
        yield from self.child2.dQuery(tape, target, symbolStack)


SymbolTable = Dict[str, State]


# CONVENIENCE FUNCTIONS FOR CONSTRUCTING GRAMMARS

def Lit(tier: str, text: str) -> State:
    return LiteralState(tier, text)

def Literalizer(tier: str) -> Callable[[str], State]:
    def literalizerFunction(text:str) -> State:
        return Lit(tier, text)
    return literalizerFunction

def Seq(*children: State) -> State:
    if len(children) == 0:
        raise StateError("Sequences must have at least 1 child")
    if len(children) == 1:
        return children[0]
    return ConcatState(children[0], Seq(*children[1:]))

def Uni(*children: State) -> State:
    if len(children) == 0:
        raise StateError("Unions must have at least 1 child")
    if len(children) == 1:
        return children[0]
    return UnionState(children[0], Uni(*children[1:]))


# Simple main for initial debugging

def debug_main():
    tier: str = "text"
    target_text: str = "hello"
    text: Callable[[str], State] = Literalizer(tier)
    grammar: State = text(target_text)
    outputs: List[StringDict] = list(grammar.generate())
    assert len(outputs) == 1, "Should have 1 result."
    assert outputs == [{tier: target_text}], f"Should have '{target_text}' on tier '{tier}'"

if __name__ == "__main__":
    debug_main()
