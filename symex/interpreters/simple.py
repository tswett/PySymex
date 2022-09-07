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

from typing import Callable, Optional, Sequence
from symex.interpreters import Interpreter
from symex.primitives import Primitive

from symex.symex import SAtom, SList, Symex
from symex.types import Binding, Closure, Environment, Function

SBuiltin = Callable[[SList, Environment], Symex]

_builtin_form_dict: dict[str, SBuiltin] = {}

def builtin_form(name: Optional[str] = None) -> Callable[[SBuiltin], SBuiltin]:
    def decorator(func: SBuiltin) -> SBuiltin:
        _builtin_form_dict[name or func.__name__] = func

        return func

    return decorator

@builtin_form()
def Quote(arg_exprs: SList, env: Environment) -> Symex:
    expr, = arg_exprs
    return expr

@builtin_form()
def Lambda(arg_exprs: SList, env: Environment) -> Symex:
    params, body = arg_exprs
    if not params.is_list:
        raise ValueError('argument list should be a list')
    params_atoms = [param.as_atom for param in params.as_list]

    return Closure(params_atoms, None, body, env).to_symex()

@builtin_form('Function')
def Function_(arg_exprs: SList, env: Environment) -> Symex:
    name, params, body = arg_exprs
    if not name.is_atom:
        raise ValueError('function name should be an atom')
    if not params.is_list:
        raise ValueError('argument list should be a list')
    params_atoms = [param.as_atom for param in params.as_list]

    return Closure(params_atoms, name.as_atom, body, env).to_symex()

@builtin_form()
def And(arg_exprs: SList, env: Environment) -> Symex:
    result: Symex = SAtom(':true')
    for exp in arg_exprs:
        result = Simple().eval_in(exp, env)
        if not result:
            return result

    return result

@builtin_form()
def Or(arg_exprs: SList, env: Environment) -> Symex:
    result: Symex = SAtom(':false')
    for exp in arg_exprs:
        result = Simple().eval_in(exp, env)
        if result:
            return result

    return result

@builtin_form()
def Cond(arg_exprs: SList, env: Environment) -> Symex:
    for pair in arg_exprs:
        condition, action = pair.as_list
        if Simple().eval_in(condition, env):
            return Simple().eval_in(action, env)

    raise ValueError('none of the conditions were true')

@builtin_form()
def Where(arg_exprs: SList, env: Environment) -> Symex:
    body, *bindings = arg_exprs

    for binding in bindings:
        name, value_expr = binding.as_list
        result = Simple().eval_in(value_expr, env)
        env = env.extend_with([Binding(name.as_atom, result)])

    return Simple().eval_in(body, env)

class Simple(Interpreter):
    def eval_in(self, expr: Symex, env: Environment) -> Symex:
        return eval_in(expr, env)

def eval_in(expr: Symex, env: Environment) -> Symex:
    if expr.is_data_atom:
        return expr
    elif expr.is_atom:
        return env[expr.as_atom]
    else:
        expr_l = expr.as_list

        if len(expr_l) == 0:
            raise ValueError('tried to evaluate an empty list')
        elif expr_l[0].is_atom and (name := expr_l[0].as_atom.text) in _builtin_form_dict:
            return _builtin_form_dict[name](expr_l[1:], env)
        else:
            values = [eval_in(exp, env) for exp in expr_l]
            func, args = values[0], values[1:]
            return apply(func, args)

def apply(func_expr: Symex, args: Sequence[Symex]) -> Symex:
    func = Function.from_symex(func_expr)

    if isinstance(func, Primitive):
        result = func.apply(args)
        return result
    elif isinstance(func, Closure):
        func_env = func.build_env(args)
        result = Simple().eval_in(func.body, func_env)
        return result
    else:
        raise ValueError('unknown type of function')
