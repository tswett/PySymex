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
from symex.symex import Symex
from symex.types import Closure, Environment, Function

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
        elif expr_l[0].is_atom and (name := expr_l[0].as_atom.text) in builtins:
            return builtins[name](expr_l[1:], env)
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
