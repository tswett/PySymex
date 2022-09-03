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

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Union, overload

class Symex:
    def __bool__(self) -> bool:
        raise NotImplementedError()

    @staticmethod
    def parse(text: str) -> Symex:
        from symex.parsing import SymexParser
        return SymexParser.parse(text)

    @property
    def is_list(self) -> bool:
        raise NotImplementedError()

    @property
    def as_list(self) -> SList:
        raise NotImplementedError()

    @property
    def is_atom(self) -> bool:
        return not self.is_list

    @property
    def as_atom(self) -> SAtom:
        raise NotImplementedError()

    @property
    def is_data_atom(self) -> bool:
        raise NotImplementedError()

    def apply(self, args: list[Symex]) -> Symex:
        from symex.types import Function
        return Function.from_symex(self).apply(args)

@dataclass(frozen=True)
class SAtom(Symex):
    text: str

    def __bool__(self) -> bool:
        return self.text != ':false'

    def __str__(self) -> str:
        return self.text

    @property
    def is_list(self) -> bool:
        return False

    @property
    def as_list(self) -> SList:
        raise ValueError("this is an atom, not a list")

    @property
    def as_atom(self) -> SAtom:
        return self

    @property
    def is_data_atom(self) -> bool:
        return len(self.text) >= 1 and self.text[0] == ':'

@dataclass(frozen=True)
class SList(Symex):
    items: list[Symex]

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
            return SList(self.items[key])
        else:
            return self.items[key]

    def __iter__(self) -> Iterator[Symex]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __str__(self) -> str:
        return '(' + ' '.join([str(item) for item in self.items]) + ')'

    @property
    def is_list(self) -> bool:
        return True

    @property
    def as_list(self) -> SList:
        return self

    @property
    def as_atom(self) -> SAtom:
        raise ValueError('this is a list, not an atom')

    @property
    def is_data_atom(self) -> bool:
        return False
