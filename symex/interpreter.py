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

from typing import Callable, ClassVar, Optional

from symex.symex import Binding, Environment, SAtom, SList, Symex

SBuiltin = Callable[[SList, Environment], Symex]

_builtin_form_dict: dict[str, SBuiltin] = {}

class BuiltinForms():
    def __init__(self) -> None:
        raise ValueError("the BuiltinForms class can't be instantiated")

    @staticmethod
    def builtin_form(name: Optional[str] = None) -> Callable[[SBuiltin], SBuiltin]:
        def decorator(func: SBuiltin) -> SBuiltin:
            _builtin_form_dict[name or func.__name__] = func

            return func

        return decorator

    @staticmethod
    @builtin_form()
    def Quote(arg_exprs: SList, env: Environment) -> Symex:
        expr, = arg_exprs
        return expr

    @staticmethod
    @builtin_form()
    def Lambda(arg_exprs: SList, env: Environment) -> Symex:
        params, body = arg_exprs
        if not params.is_list:
            raise ValueError('argument list should be a list')
        params_atoms = [param.as_atom for param in params.as_list]

        return Closure(params_atoms, None, body, env).to_symex()

    @staticmethod
    @builtin_form()
    def Function(arg_exprs: SList, env: Environment) -> Symex:
        name, params, body = arg_exprs
        if not name.is_atom:
            raise ValueError('function name should be an atom')
        if not params.is_list:
            raise ValueError('argument list should be a list')
        params_atoms = [param.as_atom for param in params.as_list]

        return Closure(params_atoms, name.as_atom, body, env).to_symex()

    @staticmethod
    @builtin_form()
    def And(arg_exprs: SList, env: Environment) -> Symex:
        result: Symex = SAtom(':true')
        for exp in arg_exprs:
            result = exp.eval_in(env)
            if not result:
                return result

        return result

    @staticmethod
    @builtin_form()
    def Or(arg_exprs: SList, env: Environment) -> Symex:
        result: Symex = SAtom(':false')
        for exp in arg_exprs:
            result = exp.eval_in(env)
            if result:
                return result

        return result

    @staticmethod
    @builtin_form()
    def Cond(arg_exprs: SList, env: Environment) -> Symex:
        for pair in arg_exprs:
            condition, action = pair.as_list
            if condition.eval_in(env):
                return action.eval_in(env)

        raise ValueError('none of the conditions were true')

    @staticmethod
    @builtin_form()
    def Where(arg_exprs: SList, env: Environment) -> Symex:
        body, *bindings = arg_exprs

        for binding in bindings:
            name, value_expr = binding.as_list
            result = value_expr.eval_in(env)
            env = env.extend_with([Binding(name.as_atom, result)])

        return body.eval_in(env)

    dict: ClassVar[dict[str, SBuiltin]] = _builtin_form_dict

del _builtin_form_dict

class Function():
    @staticmethod
    def from_symex(symex: Symex) -> Function:
        if symex.is_atom:
            raise ValueError('tried to treat an atom as a function')

        symex = symex.as_list

        if symex[0] == SAtom(':closure'):
            return Closure.from_symex(symex)
        elif symex[0] == SAtom(':primitive'):
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
        if len(args) != len(self.params):
            raise ValueError('closure got wrong number of arguments')

        bindings = [Binding(param, arg) for param, arg in zip(self.params, args)]

        if self.name is not None:
            bindings = [Binding(self.name, self.to_symex())] + bindings

        new_env = self.env.extend_with(bindings)

        return self.body.eval_in(new_env)

SFunction = Callable[[list[Symex]], Symex]

_primitive_dict: dict[str, SFunction] = {}
_primitive_env: Environment = Environment([])

@dataclass(frozen=True)
class Primitive(Function):
    name: SAtom

    @staticmethod
    def primitive_func(name: Optional[str] = None) -> Callable[[SFunction], SFunction]:
        def decorator(func: SFunction) -> SFunction:
            name_ = name or func.__name__
            new_binding = Binding(SAtom(name_), SList([SAtom(':primitive'), SAtom(name_)]))

            _primitive_dict[name_] = func
            global _primitive_env
            _primitive_env = Environment(_primitive_env.bindings + [new_binding])

            return func
        return decorator

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
        return self.dict[self.name.text]

    def apply(self, args: list[Symex]) -> Symex:
        return self.func(args)

    @staticmethod
    @primitive_func()
    def Not(args: list[Symex]) -> Symex:
        x, = args
        if x == SAtom(':false'):
            return SAtom(':true')
        else:
            return SAtom(':false')

    @staticmethod
    @primitive_func('=')
    def Equal(args: list[Symex]) -> Symex:
        if len(args) == 0:
            return SAtom(':true')

        for other in args[1:]:
            if args[0] != other:
                return SAtom(':false')

        return SAtom(':true')

    @staticmethod
    @primitive_func()
    def Cons(args: list[Symex]) -> Symex:
        head, tail = args
        return SList([head] + tail.as_list.items)

    @staticmethod
    @primitive_func()
    def Head(args: list[Symex]) -> Symex:
        list, = args
        return list.as_list[0]

    @staticmethod
    @primitive_func()
    def Tail(args: list[Symex]) -> Symex:
        list, = args
        return list.as_list[1:]

    @staticmethod
    @primitive_func()
    def List(args: list[Symex]) -> Symex:
        return SList(args)

    @staticmethod
    @primitive_func()
    def Error(args: list[Symex]) -> Symex:
        raise ValueError(f'Symex error: {args[0]}')

    dict: ClassVar[dict[str, SFunction]] = _primitive_dict
    env: ClassVar[Environment] = _primitive_env

del _primitive_dict
del _primitive_env
