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

from dataclasses import dataclass, field
from typing import Optional

from symex.symex import SAtom, SList, Symex

@dataclass(frozen=True)
class Environment():
    bindings: list[Binding] = field(default_factory=list)

    def __contains__(self, name: SAtom) -> bool:
        for binding in self.bindings:
            if binding.name == name:
                return True

        return False

    def __getitem__(self, name: SAtom) -> Symex:
        for binding in self.bindings:
            if binding.name == name:
                return binding.value

        raise ValueError(f'the name "{name.text}" is not in this environment')

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
        elif symex[0] == SAtom(':primitive'):
            from symex.primitives import Primitive
            return Primitive.from_symex(symex)
        else:
            raise ValueError('not a recognizable function')

    def apply(self, args: list[Symex]) -> Symex:
        raise NotImplementedError()

@dataclass(frozen=True)
class Closure(Function):
    params: list[SAtom]
    name: Optional[SAtom]
    body: Symex
    env: Environment

    def to_symex(self) -> SList:
        if self.name is not None:
            name_list = SList([self.name])
        else:
            name_list = SList([])

        return SList([SAtom(':closure'),
                      name_list,
                      SList(list(self.params)),
                      self.body,
                      self.env.to_symex()])

    @staticmethod
    def from_symex(symex: Symex) -> Closure:
        if symex.is_atom:
            raise ValueError('tried to treat an atom as a closure')

        tag, name_list, params, body, env = symex.as_list

        if tag != SAtom(':closure'):
            raise ValueError("this list isn't a closure")

        name_list = name_list.as_list
        if len(name_list) == 0:
            name = None
        else:
            name_symex, = name_list
            name = name_symex.as_atom

        params_atoms = [param.as_atom for param in params.as_list]

        return Closure(params_atoms, name, body, Environment.from_symex(env))

    def apply(self, args: list[Symex]) -> Symex:
        from symex.interpreters.simple import Simple

        if len(args) != len(self.params):
            raise ValueError('closure got wrong number of arguments')

        bindings = [Binding(param, arg) for param, arg in zip(self.params, args)]

        if self.name is not None:
            bindings = [Binding(self.name, self.to_symex())] + bindings

        new_env = self.env.extend_with(bindings)

        return Simple().eval_in(self.body, new_env)