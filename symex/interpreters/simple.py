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

from typing import Callable, ClassVar, Optional

from symex.primitives import primitive_env
from symex.symex import SAtom, SList, Symex
from symex.types import Binding, Closure, Environment

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
            result = eval_in(exp, env)
            if not result:
                return result

        return result

    @staticmethod
    @builtin_form()
    def Or(arg_exprs: SList, env: Environment) -> Symex:
        result: Symex = SAtom(':false')
        for exp in arg_exprs:
            result = eval_in(exp, env)
            if result:
                return result

        return result

    @staticmethod
    @builtin_form()
    def Cond(arg_exprs: SList, env: Environment) -> Symex:
        for pair in arg_exprs:
            condition, action = pair.as_list
            if eval_in(condition, env):
                return eval_in(action, env)

        raise ValueError('none of the conditions were true')

    @staticmethod
    @builtin_form()
    def Where(arg_exprs: SList, env: Environment) -> Symex:
        body, *bindings = arg_exprs

        for binding in bindings:
            name, value_expr = binding.as_list
            result = eval_in(value_expr, env)
            env = env.extend_with([Binding(name.as_atom, result)])

        return eval_in(body, env)

    dict: ClassVar[dict[str, SBuiltin]] = _builtin_form_dict

del _builtin_form_dict

def eval(expr: Symex) -> Symex:
    return eval_in(expr, primitive_env)

def eval_in(expr: Symex, env: Environment) -> Symex:
    if expr.is_data_atom:
        return expr
    elif expr.is_atom:
        return env[expr.as_atom]
    else:
        expr_l = expr.as_list

        if len(expr_l) == 0:
            raise ValueError('tried to evaluate an empty list')
        elif expr_l[0].is_atom and (name := expr_l[0].as_atom.text) in BuiltinForms.dict:
            return BuiltinForms.dict[name](expr_l[1:], env)
        else:
            values = [eval_in(exp, env) for exp in expr_l]
            func, args = values[0], values[1:]
            return func.apply(args)

def rep(input: str) -> str:
    return str(eval(Symex.parse(input)))

def eval_file(filename: str) -> Symex:
    contents = open(filename).read()
    expression = Symex.parse(contents)
    result = eval(expression)
    return result
