# This file is part of PySymex.

# PySymex is free software: you can redistribute it and/or modify it under the
# terms of version 3 of the GNU General Public License as published by the Free
# Software Foundation.

# PySymex is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Optional, overload, Union

class Symex:
    @staticmethod
    def rep(input: str) -> str:
        return str(Symex.parse(input).eval())

    @staticmethod
    def parse(text: str) -> Symex:
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

    def eval(self) -> Symex:
        return self.eval_in(Environment([]))

    def eval_in(self, env: Environment) -> Symex:
        raise NotImplementedError()

    def apply(self, args: list[Symex]) -> Symex:
        return Function.from_symex(self).apply(args)

@dataclass(frozen=True)
class SAtom(Symex):
    text: str

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

    def eval_in(self, env: Environment) -> Symex:
        if len(self.text) >= 1 and self.text[0] == ':':
            return self
        elif self in env:
            return env[self]
        else:
            raise NotImplementedError("don't know how to evaluate this atom")

@dataclass(frozen=True)
class SList(Symex):
    items: list[Symex]

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
        raise ValueError("this is a list, not an atom")

    def eval_in(self, env: Environment) -> Symex:
        if len(self) == 0:
            raise ValueError("tried to evaluate an empty list")
        elif self[0] == SAtom('Quote'):
            return self[1:]
        elif self[0] == SAtom('Lambda'):
            params, body = self[1:]
            if not params.is_list:
                raise ValueError('argument list should be a list')
            params_atoms = [param.as_atom for param in params.as_list]

            return Closure(params_atoms, body, env).to_symex()
        else:
            values = [exp.eval_in(env) for exp in self]
            func, args = values[0], values[1:]
            return func.apply(args)

@dataclass(frozen=True)
class Environment():
    bindings: list[Binding]

    def __contains__(self, name: SAtom) -> bool:
        for binding in self.bindings:
            if binding.name == name:
                return True

        return False

    def __getitem__(self, name: SAtom) -> Symex:
        for binding in self.bindings:
            if binding.name == name:
                return binding.value

        raise ValueError('the given name is not in this environment')

    def to_symex(self) -> SList:
        return SList([binding.to_symex() for binding in self.bindings])

    @staticmethod
    def from_symex(symex: Symex) -> Environment:
        if symex.is_atom:
            raise ValueError('tried to treat an atom as an environment')

        return Environment([Binding.from_symex(binding) for binding in symex.as_list])

    def extend_with(self, new_bindings: list[Binding]) -> Environment:
        return Environment(new_bindings + self.bindings)

@dataclass(frozen=True)
class Binding():
    name: SAtom
    value: Symex

    def to_symex(self) -> SList:
        return SList([self.name, self.value])

    @staticmethod
    def from_symex(symex: Symex) -> Binding:
        if symex.is_atom:
            raise ValueError('tried to treat an atom as a binding')

        name, value = symex.as_list

        return Binding(name.as_atom, value)

class Function():
    @staticmethod
    def from_symex(symex: Symex) -> Function:
        if symex.is_atom:
            raise ValueError('tried to treat an atom as a function')

        symex = symex.as_list

        if symex[0] == SAtom(':closure'):
            return Closure.from_symex(symex)

        raise ValueError('not a recognizable function')

    def apply(self, args: list[Symex]) -> Symex:
        raise NotImplementedError()

@dataclass(frozen=True)
class Closure(Function):
    params: list[SAtom]
    body: Symex
    env: Environment

    def to_symex(self) -> SList:
        return SList([SAtom(':closure'),
                      SList(list(self.params)),
                      self.body,
                      self.env.to_symex()])

    @staticmethod
    def from_symex(symex: Symex) -> Closure:
        if symex.is_atom:
            raise ValueError('tried to treat an atom as a closure')

        tag, params, body, env = symex.as_list

        if tag != SAtom(':closure'):
            raise ValueError("this list isn't a closure")

        params_atoms = [param.as_atom for param in params.as_list]

        return Closure(params_atoms, body, Environment.from_symex(env))

    def apply(self, args: list[Symex]) -> Symex:
        if len(args) != len(self.params):
            raise ValueError('closure got wrong number of arguments')

        new_env = self.env.extend_with([Binding(param, arg)
                                        for param, arg
                                        in zip(self.params, args)])

        return self.body.eval_in(new_env)

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