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
from typing import Callable, Optional

from symex.interpreters.simple import Function
from symex.symex import Binding, Environment, SAtom, SList, Symex

SFunction = Callable[[list[Symex]], Symex]

primitive_dict: dict[str, SFunction] = {}
primitive_env = Environment([])

@dataclass(frozen=True)
class Primitive(Function):
    name: SAtom

    def to_symex(self) -> SList:
        return SList([SAtom(':primitive'), self.name])

    @staticmethod
    def from_symex(symex: Symex) -> Primitive:
        if symex.is_atom:
            raise ValueError('tried to treat an atom as a primitive function')
        
        tag, name = symex.as_list

        if tag != SAtom(':primitive'):
            raise ValueError("this list isn't a primitive function")

        return Primitive(name.as_atom)

    @property
    def func(self) -> SFunction:
        return primitive_dict[self.name.text]

    def apply(self, args: list[Symex]) -> Symex:
        return self.func(args)

def primitive_func(name: Optional[str] = None) -> Callable[[SFunction], SFunction]:
    def decorator(func: SFunction) -> SFunction:
        name_ = name or func.__name__
        new_binding = Binding(SAtom(name_), SList([SAtom(':primitive'), SAtom(name_)]))

        primitive_dict[name_] = func
        global primitive_env
        primitive_env = Environment(primitive_env.bindings + [new_binding])

        return func
    return decorator

@primitive_func()
def Not(args: list[Symex]) -> Symex:
    x, = args
    if x == SAtom(':false'):
        return SAtom(':true')
    else:
        return SAtom(':false')

@primitive_func('=')
def Equal(args: list[Symex]) -> Symex:
    if len(args) == 0:
        return SAtom(':true')

    for other in args[1:]:
        if args[0] != other:
            return SAtom(':false')

    return SAtom(':true')

@primitive_func()
def Cons(args: list[Symex]) -> Symex:
    head, tail = args
    return SList([head] + tail.as_list.items)

@primitive_func()
def Head(args: list[Symex]) -> Symex:
    list, = args
    return list.as_list[0]

@primitive_func()
def Tail(args: list[Symex]) -> Symex:
    list, = args
    return list.as_list[1:]

@primitive_func()
def List(args: list[Symex]) -> Symex:
    return SList(args)

@primitive_func()
def Error(args: list[Symex]) -> Symex:
    raise ValueError(f'Symex error: {args[0]}')

@primitive_func('Is-Data-Atom')
def IsDataAtom(args: list[Symex]) -> Symex:
    x, = args
    if x.is_data_atom:
        return SAtom(':true')
    else:
        return SAtom(':false')
