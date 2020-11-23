from __future__ import annotations

from util import StringDict, Gen, BitSet

from typing import Final, Optional, List, Dict
from abc import ABC, abstractmethod

""" Outputs

The outputs of this algorithm are kept as tries, since that's the natural shape
of a set of outputs from a non-deterministic parsing algorithm.  (E.g., if we've
already output "fooba", and at the next state we could either output "r" or "z",
then just having "r" and "z" point to that previous output is both less effort
and less space than copying it twice and concatenating it.  Especially if "z"
ends up being a false path and we end up discarding it; that would mean we had
copied/ concatenated for nothing.)   

It used to be that we just kept every tape output in one trie (like an output
might have characters on different tapes interleaved).  That's fine when it's
guaranteed that every concatenation succeeds (like for string concatenation),
but when it's something like flag concatenation (which can fail), that means we
have to search backwards through the trie to find the most recent output on the
relevant tape.  So now, outputs are segregated by tape. A SingleTapeOutput
represents the output on a given tape, and then there's a separate object that
represents a collection of them (by keeping a pointer to the appropriate output
along each tape).

TODO: There's currently some conceptual duplication between these Outputs and
the various Tape objects, which store *information* about tapes (like their
names and vocabs) without storing any actual outputs onto those tapes.  Each
Output is associated with a particular Tape, there are collections of both
corresponding to each other, etc.  We should eventually refactor these so that
there's only one hierarchy of objects, "tapes" to which you can write and also
know their own information.
"""

class SingleTapeOutput:
    """ Output for a single Tape """

    def __init__(self, tape: Tape, token: Token, prev: Optional[SingleTapeOutput]) -> None:
        self._tape: Tape = tape
        self._token: Token = token
        self._prev: Optional[SingleTapeOutput] = prev

    def add(self, tape: Tape, token: Token) -> SingleTapeOutput:
        if tape.tapeName != self._tape.tapeName:
            raise TapeError(f"Incompatible tapes: {tape.tapeName}, {self._tape.tapeName}")
        return SingleTapeOutput(tape, token, self)

    def getStrings(self) -> Gen[str]:
        prevStrings: List[str] = [""]
        if self._prev is not None:
            prevStrings = list(self._prev.getStrings())
        
        for s in prevStrings:
            for c in self._tape.fromBits(self._tape.tapeName, self._token.bits):
                yield s + c

class MultiTapeOutput:
    """
    Multi tape output
    
    This stores a collection of outputs on different tapes, by storing a
    collection of pointers to them. When you add a <tape, char> pair to it (say,
    <text,b>), you return a new MultiTapeOutput that now points to a new
    SingleTapeOutput corresponding to "text" -- the new one with "b" added --
    and keep all the old pointers the same.
    """
    def __init__(self):
        self.singleTapeOutputs: Dict[str, SingleTapeOutput] = {}

    def add(self, tape: Tape, token: Token) -> MultiTapeOutput:
        if tape.numTapes == 0:
            return self

        result: MultiTapeOutput = MultiTapeOutput()
        result.singleTapeOutputs.update(self.singleTapeOutputs)
        prev: Optional[SingleTapeOutput] = self.singleTapeOutputs.get(tape.tapeName)
        result.singleTapeOutputs[tape.tapeName] = SingleTapeOutput(tape, token, prev)
        return result

    def toStrings(self) -> List[StringDict]:
        """ Return a join of the outputs for the individual tapes.
            Example: With tapes named tape1, tape2, tape3, whose outputs are
                tape1: foobar, foobaz
                tape2: a, b
                tape3: 3333
            Return the list:
            [ {'tape1': 'foobar', 'tape2': 'a', 'tape3': '3333'},
              {'tape1': 'foobaz', 'tape2': 'b', 'tape3': '3333'},
              {'tape1': 'foobar', 'tape2': 'a', 'tape3': '3333'},
              {'tape1': 'foobaz', 'tape2': 'b', 'tape3': '3333'} ]
        """
        results: List[StringDict] = [{}]
        for tapeName, tape in self.singleTapeOutputs.items():
            newResults: List[StringDict] = []
            for s in tape.getStrings():
                for result in results:
                    newResult: StringDict = result.copy()
                    newResult[tapeName] = s
                    newResults.append(newResult)
            results = newResults
        return results


class TapeError(Exception):
    """ Exception raised for tape mismatch errors.

    Attributes:
        msg: explanatory error message 
    """
    def __init__(self, msg: str) -> None:
        self.msg = msg


class Tape(ABC):
    """
    Tape: Abstract Base Class for all tape classes
    
    This encapsulates information about a tape or set of tapes (like what its
    name is, what its possible vocabulary is, what counts as concatenation and
    matching, etc.).  It doesn't, however, encapsulate a tape in the sense of
    keeping a sequence of character outputs; that would be encapsulated by the
    Output objects above.

    TODO: Refactor Outputs and Tapes so that they're all one kind of object,
    because currently we're keeping a duplicated hierarchy in which the Output
    and Tape class hierarchies mirror each other.
    """
    def __init__(self, tapeName: str, numTapes: int) -> None:
        self._tapeName = tapeName
        self._numTapes = numTapes

    @property
    def tapeName(self) -> str:
        return self._tapeName

    @property
    def numTapes(self) -> int:
        return self._numTapes

    def add(self, str1: str, str2: str) -> List[str]:
        raise NotImplementedError

    def match(self, str1: Token, str2: Token) -> Token:
        raise NotImplementedError

    def any(self) -> Token:
        raise NotImplementedError

    def plus(self, tapeName: str, other: BitSet) -> Gen[Tape]:
        raise NotImplementedError

    def times(self, tapeName: str, other: BitSet) -> Gen[Tape]:
        raise NotImplementedError

    def tokenize(self, tapeName: str, string: str) -> List[Token]:
        raise NotImplementedError

    @abstractmethod
    def matchTape(self, tapeName: str) -> Optional[Tape]:
        pass

    @abstractmethod
    def toBits(self, tapeName: str, char: str) -> BitSet:
        pass

    @abstractmethod
    def fromBits(self, tapeName: str, bits: BitSet) -> List[str]:
        pass

class Token:
    """ Token
    
    This encapsulates a token, so that parsers need not necessarily know how,
    exactly, a token is implemented. Right now we only have one kind of token,
    strings implemented as BitSets, but eventually this should be an abstract
    class with (e.g.) StringToken, maybe FlagToken, ProbToken and/or LogToken
    (for handling weights), etc.
    """
    def __init__(self, bits: BitSet) -> None:
        self.bits = bits

    def and_(self, other: Token) -> Token:
        return Token(self.bits & other.bits)
    
    def andNot(self, other: Token) -> Token:
        return Token(self.bits & ~other.bits)
    
    def isEmpty(self) -> bool:
        return not self.bits.any()

MAX_NUM_CHARS: Final[int] = 32
ANY_CHAR: Final[Token] = Token(~BitSet(MAX_NUM_CHARS))
NO_CHAR: Final[Token] = Token(BitSet())

class StringTape(Tape):
    """ String tape class implementation

    A tape containing strings; the basic kind of tape and (right now) the only
    one we really use. (Besides a TapeCollection, which implements Tape but is
    really used for a different situation.)
    """
    def __init__(self,
                 tapeName: str, 
                 current: Optional[Token] = None,
                 prev: Optional[StringTape] = None,
                 strToIndex: Dict[str, int] = {},
                 indexToStr: Dict[int, str] = {}) -> None:
        super().__init__(tapeName, 1)
        self.current = current
        self.prev = prev
        self.strToIndex = strToIndex
        self.indexToStr = indexToStr

    def append(self, token: Token) -> StringTape:
        return StringTape(self.tapeName, token, self,
                          self.strToIndex, self.indexToStr)

    def getStrings(self) -> Gen[str]:
        prevStrings: List[str]
        if self.prev is not None:
            prevStrings.extend(self.prev.getStrings())
        
        if self.current is None:
            yield from prevStrings

        for s in prevStrings:
            for c in self.fromBits(self.tapeName, self.current.bits):
                yield s + c

    def matchTape(self, tapeName: str) -> Optional[Tape]:
        return self if tapeName == self.tapeName else None

    def any(self) -> Token:
        # return Token(~BitSet(len(self.strToIndex)))
        return Token(~BitSet(MAX_NUM_CHARS))

    def add(self, str1: str, str2: str) -> List[str]:
        return [str1 + str2]

    def match(self, str1: Token, str2: Token) -> Token:
        return str1.and_(str2)

    def tokenize(self, tapeName: str, string: str) -> List[Token]:
        if tapeName != self.tapeName:
            raise TapeError(f"Trying to add a character from tape {tapeName} \
                              to tape {self.tapeName}")
        
        results: List[Token] = []
        for c in string:
            index: Optional[int] = self.strToIndex.get(c)
            if index is None:
                index = self.registerToken(c)
            newToken: Token = Token(self.toBits(tapeName, c))
            results.append(newToken)
        return results

    def registerToken(self, token: str) -> int:
        index: Final[int] = len(self.strToIndex)
        self.strToIndex[token] = index
        self.indexToStr[index] = token
        return index

    def toBits(self, tapeName: str, char: str) -> BitSet:
        if tapeName != self.tapeName:
            raise TapeError(f"Trying to get bits on tape {tapeName} \
                              from tape ${self.tapeName}")
        
        # result: BitSet = BitSet(len(self.strToIndex))
        result: BitSet = BitSet(MAX_NUM_CHARS)
        index: Final[Optional[int]] = self.strToIndex.get(char)
        if index is None:
            return result
        result[index] = 1
        return result
    
    def fromBits(self, tapeName: str, bits: BitSet) -> List[str]:
        if tapeName != self.tapeName:
            raise TapeError(f"Trying to get bits on tape {tapeName} \
                              from tape ${self.tapeName}")

        result: List[str] = []
        for i in range(len(bits)):
            if bits[i]:
                char: Optional[str] = self.indexToStr.get(i)
                if char is None:
                    break
                result.append(char)
        return result

class FlagTape(StringTape):
    """ Flag tape class implementation.

    A tape containing flags, roughly identical to a "U" flag in XFST/LEXC.  
    This uses a different method for "add" than a normal string tape; you can
    always concatenate a string to a string, but trying to add a flag to a
    different flag will fail.

    At the moment this isn't used anywhere.
    """
    def add(self, oldResults: str, newResult: str) -> List[str]:
        if oldResults == "" or oldResults == newResult:
            return [newResult]
        return []

    def tokenize(self, tapeName: str, string: str) -> List[Token]:
        if tapeName != self.tapeName:
            raise TapeError(f"Trying to add a character from tape {tapeName} \
                              to tape {self.tapeName}")

        if (string not in self.strToIndex):
            self.registerToken(string)
        return [Token(self.toBits(tapeName, string))]
    
class TapeCollection(Tape):
    """ Collection of Tapes
 
    This contains information about all the tapes.  When we do a "free query" in
    the state machine, what we're saying is "match anything on any tape".
    Eventually, something's going to match on a particular tape, so we have to
    have that information handy for all tapes.  (That is to say, something like
    a LiteralState knows what tape it cares about only as a string, say, "text".
    In a constrained query, we pass in a normal StringTape object, and if it's
    the "text" tape, matchTape("text") succeeds and returns itself, and if it
    doesn't, matchTape("text") fails.  In a free query, we pass in one of these
    objects, and when we matchTape("text"), we return the StringTape
    corresponding to "text".  That's why we need an object that collects all of
    them, so we can return the appropriate one when it's needed.)
    """
    def __init__(self) -> None:
        self._tapes: Dict[str, Tape] = {}

    @property
    def numTapes(self) -> int:
        return len(self._tapes)
    
    def addTape(self, tape: Tape) -> None:
        self._tapes[tape.tapeName] = tape

    @property
    def tapeName(self) -> str:
        if len(self._tapes) == 0:
            return "__NO_TAPE__"
        return "__ANY_TAPE__"

    def tokenize(self, tapeName: str, string: str) -> List[Token]:
        if tapeName not in self._tapes:
            self._tapes[tapeName] = StringTape(tapeName)
        return self._tapes[tapeName].tokenize(tapeName, string)

    def matchTape(self, tapeName: str) -> Optional[Tape]:
        return self._tapes.get(tapeName)

    def toBits(self, tapeName: str, char: str) -> BitSet:
        if tapeName not in self._tapes:
            raise TapeError(f"Undefined tape: {tapeName}")
        return self._tapes[tapeName].toBits(tapeName, char)

    def fromBits(self, tapeName: str, bits: BitSet) -> List[str]:
        if tapeName not in self._tapes:
            raise TapeError(f"Undefined tape: {tapeName}")
        return self._tapes[tapeName].fromBits(tapeName, bits)

class RenamedTape(Tape):
    """ RenamedTapes are necessary for RenameStates to work properly.
    
    From the point of view of any particular state, it believes that particular
    tapes have particular names, e.g. "text" or "gloss".  However, because
    renaming is an operator of our relational algebra, different states may be
    referred to by different names in different parts of the grammar.  

    (For example, consider a composition between two FSTS, {"up":"lr",
    "down":"ll"} and {"up":"ll", "down":"lh"}.  In order to express their
    composition as a "join", we have to make it so that the first "down" and the
    second "up" have the same name.  Renaming does that.

    The simplest way to get renaming, so that each state doesn't have to
    understand the name structure of the larger grammar, is for RenameStates to
    wrap tapes in a simple adaptor class that makes it seem as if an existing
    tape has a new name.  That way, any child of a RenameState can (for example)
    ask for the vocabulary of the tape it thinks is called "down", even if
    outside of that RenameState the tape is called "text".  
    """
    def __init__(self, child: Tape, fromTape: str, toTape: str) -> None:
        super().__init__(child.tapeName, child.numTapes)
        self._child = child
        self._fromTape = fromTape
        self._toTape = toTape

    @property
    def tapeName(self) -> str:
        return self._child.tapeName

    @property
    def numTapes(self) -> int:
        return self._child.numTapes
    
    def any(self) -> Token:
        return self._child.any()

    def add(self, str1: str, str2: str) -> List[str]:
        return self._child.add(str1, str2)

    def match(self, str1: Token, str2: Token) -> Token:
        return self._child.match(str1, str2)

    def _adjustTapeName(self, tapeName: str) -> str:
        return self._toTape if tapeName == self._fromTape else tapeName
    
    def matchTape(self, tapeName: str) -> Optional[Tape]:
        tapeName = self._adjustTapeName(tapeName)
        newChild: Final[Optional[Tape]] = self._child.matchTape(tapeName)
        if newChild is None:
            return None
        return RenamedTape(newChild, self._fromTape, self._toTape)

    def tokenize(self, tapeName: str, string: str) -> List[Token]:
        tapeName = self._adjustTapeName(tapeName)
        return self._child.tokenize(tapeName, string)

    def toBits(self, tapeName: str, char: str) -> BitSet:
        tapeName = self._adjustTapeName(tapeName)
        return self._child.toBits(tapeName, char)

    def fromBits(self, tapeName: str, bits: BitSet) -> List[str]:
        tapeName = self._adjustTapeName(tapeName)
        return self._child.fromBits(tapeName, bits)