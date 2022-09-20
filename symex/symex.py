# This file is part of PySymex.
#
# PySymex is free software: you can redistribute it and/or modify it under the
# terms of version 3 of the GNU General Public License as published by the Free
# Software Foundation.
#
# PySymex is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# Copyright 2022 by Tanner Swett.

"""Fundamental Symex types

This module defines three types. The basic type is `Symex`, which represents a
symbolic expression (S-expression). There are two types of `Symex`: an `SAtom`
is an atom (basically just a string), and an `SList` is a list.

As of this writing, this Lisp implementation is being migrated from using Python
lists to using custom linked lists. In the near future, support for "improper
lists" (lists which terminate in something other than the empty list) will be
added.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Sequence, Union, overload

class Symex:
    """A symbolic expression"""
    def __bool__(self) -> bool:
        raise NotImplementedError()

    @staticmethod
    def parse(text: str) -> Symex:
        from symex.parsing import SymexParser
        return SymexParser.parse(text)

    @property
    def is_data_atom(self) -> bool:
        raise NotImplementedError()

@dataclass(frozen=True)
class SAtom(Symex):
    """An S-expression which is an atom"""
    text: str

    def __bool__(self) -> bool:
        return self.text != ':false'

    def __str__(self) -> str:
        return self.text

    @property
    def is_data_atom(self) -> bool:
        return len(self.text) >= 1 and self.text[0] == ':'

@dataclass(frozen=True)
class SList(Symex):
    """An S-expression which is a linked list"""

    __match_args__ = ('items',)

    def __bool__(self) -> bool:
        return True

    @overload
    def __getitem__(self, key: slice) -> SList:
        raise NotImplementedError()

    @overload
    def __getitem__(self, key: int) -> Symex:
        raise NotImplementedError()

    def __getitem__(self, key: Union[int, slice]) -> Symex:
        if isinstance(key, slice):
            raise NotImplementedError('this form of SList.__getitem__ has not been implemented yet')

        if key < 0:
            raise NotImplementedError('this form of SList.__getitem__ has not been implemented yet')

        current = self
        while key > 0:
            if isinstance(current, SConsCell):
                current = current.tail
            else:
                raise IndexError('SList index out of range')
            key -= 1

        if isinstance(current, SConsCell):
            return current.head
        else:
            raise IndexError('SList index out of range')

    def __iter__(self) -> Iterator[Symex]:
        current = self
        while isinstance(current, SConsCell):
            yield current.head
            current = current.tail

    def __len__(self) -> int:
        raise NotImplementedError()

    def __str__(self) -> str:
        return '(' + ' '.join([str(item) for item in self]) + ')'

    @property
    def is_data_atom(self) -> bool:
        return False

    # TODO: This implementation of `items` is no good in the long run.
    # We shouldn't ever have to convert an SList to a tuple.
    @property
    def items(self) -> tuple[Symex, ...]:
        return tuple(self)

@dataclass(frozen=True)
class SEmptyList(SList):
    """An S-expression which is the empty list"""

    def __len__(self) -> int:
        return 0

@dataclass(frozen=True)
class SConsCell(SList):
    """An S-expression which is a cons cell
    
    A cons cell is usually used to represent a linked list, where the `head`
    element is the first element of the list, and the `tail` element is another
    list containing all of the remaining elements.
    
    Traditionally, `head` is called `car` and `tail" is called `cdr`.
    """
    head: Symex
    tail: SList
    length: int

    def __init__(self, head: Symex, tail: SList):
        object.__setattr__(self, 'head', head)
        object.__setattr__(self, 'tail', tail)
        length = len(tail) + 1
        object.__setattr__(self, 'length', length)

    def __len__(self) -> int:
        return self.length

def slist(sequence: Sequence[Symex]) -> SList:
    result: SList = SEmptyList()

    for item in sequence[::-1]:
        result = SConsCell(item, result)

    return result
