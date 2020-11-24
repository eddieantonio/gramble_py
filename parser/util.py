from __future__ import annotations

from typing import TypeVar, Generator, Dict
from bitarray import bitarray

# Gen[T]
Gen_T = TypeVar('Gen_T')
Gen = Generator[Gen_T, None, None]

StringDict = Dict[str, str]

# BitSet cannot extend bitarray due to a bug in the C implementation of bitarray
# preventing us from calling super().__init__ with arguments.
# class BitSet(bitarray):
#     """ BitSet wraps bitarray """
#     def __init__(self, initializer=1, /, *args, **kwargs) -> None:
#         super().__init__(initializer, *args, **kwargs)
#         if type(initializer) == int:
#             self.setall(0)

class BitSet():
    """ BitSet wraps bitarray """
    def __init__(self, initializer=1, /, *args, **kwargs) -> None:
        self.bitset = bitarray(initializer, *args, **kwargs)
        if type(initializer) == int:
            self.bitset.setall(0)

    def __repr__(self):
        return f"BitSet{self.bitset.__repr__()[8:]}"

    def __str__(self):
        return f"BitSet{self.bitset.__str__()[8:]}"

    def __len__(self):
        return self.bitset.__len__()

    def __contains__(self, key):
        return self.bitset.__contains__(key)

    def __iter__(self):
        return self.bitset.__iter__()

    def __getitem__(self, key):
        return self.bitset.__getitem__(key)

    def __setitem__(self, key, value):
        return self.bitset.__setitem__(key, value)

    def __delitem__(self, key):
        return self.bitset.__delitem__(key)

    def __add__(self, value):
        if type(value) is BitSet:
            value = value.bitset
        return BitSet(self.bitset.__add__(value))

    def __mul__(self, value):
        if type(value) is BitSet:
            value = value.bitset
        return BitSet(self.bitset.__mul__(value))

    def __and__(self, value):
        if type(value) is BitSet:
            value = value.bitset
        return BitSet(self.bitset.__and__(value))

    def __or__(self, value):
        if type(value) is BitSet:
            value = value.bitset
        return BitSet(self.bitset.__or__(value))
 
    def __xor__(self, value):
        if type(value) is BitSet:
            value = value.bitset
        return BitSet(self.bitset.__xor__(value))

    def __iadd__(self, value):
        if type(value) is BitSet:
            value = value.bitset
        return BitSet(self.bitset.__iadd__(value))

    def __imul__(self, value):
        if type(value) is BitSet:
            value = value.bitset
        return BitSet(self.bitset.__imul__(value))

    def __iand__(self, value):
        if type(value) is BitSet:
            value = value.bitset
        return BitSet(self.bitset.__iand__(value))

    def __ior__(self, value):
        if type(value) is BitSet:
            value = value.bitset
        return BitSet(self.bitset.__ior__(value))
 
    def __ixor__(self, value):
        if type(value) is BitSet:
            value = value.bitset
        return BitSet(self.bitset.__ixor__(value))

    def __invert__(self):
        return BitSet(self.bitset.__invert__())

    def __lt__(self, value):
        if type(value) is BitSet:
            value = value.bitset
        return self.bitset.__lt__(value)

    def __le__(self, value):
        if type(value) is BitSet:
            value = value.bitset
        return self.bitset.__le__(value)

    def __eq__(self, value):
        if type(value) is BitSet:
            value = value.bitset
        return self.bitset.__eq__(value)

    def __ne__(self, value):
        if type(value) is BitSet:
            value = value.bitset
        return self.bitset.__ne__(value)

    def __gt__(self, value):
        if type(value) is BitSet:
            value = value.bitset
        return self.bitset.__gt__(value)

    def __ge__(self, value):
        if type(value) is BitSet:
            value = value.bitset
        return self.bitset.__ge__(value)

    def any(self):
        """ Return True if any bit in the BitSet is True. """
        return self.bitset.any()

    def all(self):
        """ Return True if all bits in the BitSet are True. """
        return self.bitset.all()
