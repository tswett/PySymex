from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, List, Optional

class Symex:
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Symex):
            return False

        if isinstance(self, SList) and isinstance(other, SList):
            if len(self) != len(other):
                return False
            return all([x == y for x, y in zip(self, other)])

        if isinstance(self, SAtom) and isinstance(other, SAtom):
            return self.text == other.text

        return False

    @staticmethod
    def rep(input: str) -> str:
        return str(Symex.parse(input).eval())

    @staticmethod
    def parse(text: str) -> Symex:
        return SymexParser.parse(text)

    def eval(self) -> Symex:
        return self.eval_in(Environment([]))

    def eval_in(self, env: Environment) -> Symex:
        raise NotImplementedError()

@dataclass(eq=False, frozen=True)
class SAtom(Symex):
    text: str

    def __str__(self) -> str:
        return self.text

    @property
    def is_list(self) -> bool:
        return False

    def eval_in(self, env: Environment) -> Symex:
        if len(self.text) >= 1 and self.text[0] == ':':
            return self
        else:
            raise NotImplementedError("don't know how to evaluate this atom")

@dataclass(eq=False, frozen=True)
class SList(Symex):
    items: List[Symex]

    def __iter__(self) -> Iterator[Symex]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __str__(self) -> str:
        return '(' + ' '.join([str(item) for item in self.items]) + ')'

    @property
    def is_list(self) -> bool:
        return True

class Environment(SList):
    pass

class SymexParser():
    def __init__(self, text: str):
        self.text: str = text
        self.next_index: int = 0

    @staticmethod
    def parse(text: str) -> Symex:
        parser = SymexParser(text)
        result = parser.parse_with_tail()
        parser.consume_whitespace()

        if parser.next_char is None:
            return result
        else:
            raise ValueError('extra text was present after the end of the expression')

    def parse_with_tail(self) -> Symex:
        self.consume_whitespace()

        if self.next_char is None:
            raise ValueError('unexpected end of input')

        if self.next_char == '(':
            return self.parse_list_with_tail()

        if self.is_atom_char(self.next_char):
            return self.parse_atom_with_tail()

        raise ValueError('failed to find a recognizable character')

    def parse_atom_with_tail(self) -> SAtom:
        self.consume_whitespace()

        result_str = ''

        while (next_char := self.next_char) is not None and self.is_atom_char(next_char):
            result_str += next_char
            self.next_index += 1

        if result_str == '':
            raise ValueError('failed to find an atom character')
        else:
            return SAtom(result_str)

    @staticmethod
    def is_atom_char(char: str) -> bool:
        return char.isalnum() or char in "_-:?"

    def parse_list_with_tail(self) -> SList:
        self.consume_whitespace()

        if self.next_char == '(':
            self.next_index += 1
        else:
            raise ValueError('failed to find an opening parenthesis')

        result_list = []

        self.consume_whitespace()

        while self.next_char != ')':
            item = self.parse_with_tail()
            result_list.append(item)
            self.consume_whitespace()

        if self.next_char == ')':
            self.next_index += 1
            return SList(result_list)
        else:
            raise ValueError('failed to find a closing parenthesis')

    def consume_whitespace(self) -> None:
        while ((next_char := self.next_char) is not None and
               (next_char.isspace() or next_char == ';')):
            if self.next_char == ';':
                while self.next_char != '\n' and self.next_char is not None:
                    self.next_index += 1
            else:
                self.next_index += 1

    @property
    def next_char(self) -> Optional[str]:
        if self.next_index == len(self.text):
            return None
        else:
            return self.text[self.next_index]