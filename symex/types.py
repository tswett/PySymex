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
from typing import Optional, Sequence

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
        match symex:
            case SAtom(_):
                raise ValueError('tried to treat an atom as an environment')
            case SList(list):
                return Environment([Binding.from_symex(binding) for binding in list])
            case _:
                raise ValueError('unknown type of symex')

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
        match symex:
            case SAtom():
                raise ValueError('tried to treat an atom as a binding')
            case SList((SAtom() as name, value)):
                return Binding(name, value)
            case _:
                raise ValueError('not a well-formed binding')

class Function():
    @staticmethod
    def from_symex(symex: Symex) -> Function:
        match symex:
            case SAtom():
                raise ValueError('tried to treat an atom as a function')
            case SList((SAtom(':closure'), *_)):
                return Closure.from_symex(symex)
            case SList((SAtom(':primitive'), *_)):
                from symex.primitives import Primitive
                return Primitive.from_symex(symex)
            case _:
                raise ValueError('not a recognizable function')

@dataclass(frozen=True)
class Closure(Function):
    params: tuple[SAtom, ...]
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
        match symex:
            case SAtom(_):
                raise ValueError('this is an atom, not a closure')
            case SList((SAtom(':closure'), SList(name_list), SList(params), body, env)):
                pass
            case SList((SAtom(':closure'), *_)):
                raise ValueError("this closure isn't well-formed")
            case _:
                raise ValueError("this isn't a closure")

        name: Optional[SAtom]

        match name_list:
            case (SAtom() as name,):
                pass
            case ():
                name = None
            case _:
                raise ValueError("this closure's name list isn't well-formed")

        def assert_atom(param: Symex) -> SAtom:
            match param:
                case SAtom():
                    return param
                case _:
                    raise ValueError("this parameter isn't an atom")

        params_atoms = tuple(assert_atom(param) for param in params)

        return Closure(params_atoms, name, body, Environment.from_symex(env))

    @staticmethod
    def from_defining_parts(params: SList,
                            name: Optional[SAtom],
                            body: Symex,
                            env: Environment) -> Closure:
        def assert_atom(param: Symex) -> SAtom:
            match param:
                case SAtom():
                    return param
                case _:
                    raise ValueError("this parameter isn't an atom")
        
        params_atoms = tuple((assert_atom(param) for param in params))

        return Closure(params_atoms, name, body, env)

    def build_env(self, args: Sequence[Symex]) -> Environment:
        self_symex = self.to_symex()

        if len(args) != len(self.params):
            raise ValueError('closure got wrong number of arguments')

        bindings = [Binding(param, arg) for param, arg in zip(self.params, args)]

        if self.name is not None:
            bindings = [Binding(self.name, self_symex)] + bindings

        new_env = self.env.extend_with(bindings)

        return new_env
