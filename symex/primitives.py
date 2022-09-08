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
from typing import Callable, Optional, Sequence

from symex.symex import SAtom, SList, Symex
from symex.types import Binding, Environment, Function

SFunction = Callable[[Sequence[Symex]], Symex]

primitive_dict: dict[str, SFunction] = {}
primitive_env = Environment([])

@dataclass(frozen=True)
class Primitive(Function):
    name: SAtom

    def to_symex(self) -> SList:
        return SList([SAtom(':primitive'), self.name])

    @staticmethod
    def from_symex(symex: Symex) -> Primitive:
        match symex:
            case SList((SAtom(':primitive'), SAtom() as name)):
                return Primitive(name)
            case SList((SAtom(':primitive'), *_)):
                raise ValueError("this is an ill-formed primitive function")
            case _:
                raise ValueError("this isn't a primitive function")

    @property
    def func(self) -> SFunction:
        return primitive_dict[self.name.text]

    def apply(self, args: Sequence[Symex]) -> Symex:
        return self.func(args)

def add_primitive(name: str, value: Symex) -> None:
    new_binding = Binding(SAtom(name), value)

    global primitive_env
    primitive_env = Environment(primitive_env.bindings + [new_binding])

def primitive_func(name: Optional[str] = None) -> Callable[[SFunction], SFunction]:
    def decorator(func: SFunction) -> SFunction:
        name_ = name or func.__name__
        value = SList([SAtom(':primitive'), SAtom(name_)])

        primitive_dict[name_] = func
        add_primitive(name_, value)

        return func
    return decorator

@primitive_func()
def Not(args: Sequence[Symex]) -> Symex:
    x, = args
    if x == SAtom(':false'):
        return SAtom(':true')
    else:
        return SAtom(':false')

@primitive_func('=')
def Equal(args: Sequence[Symex]) -> Symex:
    if len(args) == 0:
        return SAtom(':true')

    for other in args[1:]:
        if args[0] != other:
            return SAtom(':false')

    return SAtom(':true')

@primitive_func()
def Cons(args: Sequence[Symex]) -> Symex:
    match args:
        case (head, SList(tail)):
            return SList((head,) + tail)
        case (_, _):
            raise ValueError("the Cons function got something that isn't a list")
        case _:
            raise ValueError("the Cons function got the wrong number of arguments")

@primitive_func()
def Head(args: Sequence[Symex]) -> Symex:
    match args:
        case (arg,):
            match arg:
                case SList((head, *_)):
                    return head
                case SList(()):
                    raise ValueError("the Head function got an empty list")
                case _:
                    raise ValueError("the Head function got something that isn't a list")
        case ():
            raise ValueError("the Head function didn't get any arguments")
        case _:
            raise ValueError("the Head function got too many arguments")

@primitive_func()
def Tail(args: Sequence[Symex]) -> Symex:
    match args:
        case (arg,):
            match arg:
                case SList((_, *tail)):
                    return SList(tail)
                case SList(()):
                    raise ValueError("the Tail function got an empty list")
                case _:
                    raise ValueError("the Tail function got something that isn't a list")
        case ():
            raise ValueError("the Tail function didn't get any arguments")
        case _:
            raise ValueError("the Tail function got too many arguments")

@primitive_func()
def List(args: Sequence[Symex]) -> Symex:
    return SList(args)

@primitive_func()
def Error(args: Sequence[Symex]) -> Symex:
    raise ValueError(f'Symex error: {args[0]}')

@primitive_func('Is-Data-Atom')
def IsDataAtom(args: Sequence[Symex]) -> Symex:
    x, = args
    if x.is_data_atom:
        return SAtom(':true')
    else:
        return SAtom(':false')

add_primitive('Nil', SList([]))
