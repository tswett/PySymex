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

from typing import Sequence

from symex.interpreters import Interpreter
from symex.interpreters.simple_builtins import builtins
from symex.primitives import Primitive
from symex.symex import SAtom, SList, Symex
from symex.types import Closure, Environment, Function

class Simple(Interpreter):
    def eval_in(self, expr: Symex, env: Environment) -> Symex:
        return eval_in(expr, env)

def eval_in(expr: Symex, env: Environment) -> Symex:
    match expr:
        case _ if expr.is_data_atom:
            return expr
        case SAtom():
            return env[expr]
        case SList(()):
            raise ValueError('tried to evaluate an empty list')
        case SList((SAtom(name), *arg_exprs)) if name in builtins:
            return builtins[name](arg_exprs, env)
        case SList(symexes):
            values = [eval_in(exp, env) for exp in symexes]
            func, args = values[0], values[1:]
            return apply(func, args)
        case _:
            raise ValueError('unknown type of symex')

    raise ValueError('no pattern matched')

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
