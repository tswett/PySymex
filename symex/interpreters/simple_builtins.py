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

from typing import Callable, Optional, Sequence

from symex.interpreters import Interpreter
from symex.symex import SAtom, SList, Symex
from symex.types import Binding, Closure, Environment

# TODO eliminate duplication of make_closure between simple_builtins and machine_builtins
def make_closure(params: SList, name: Optional[SAtom], body: Symex, env: Environment) -> Symex:
    def assert_atom(param: Symex) -> SAtom:
        match param:
            case SAtom():
                return param
            case _:
                raise ValueError("this parameter isn't an atom")
    
    params_atoms = tuple((assert_atom(param) for param in params))

    return Closure(params_atoms, name, body, env).to_symex()

SBuiltin = Callable[[Sequence[Symex], Environment], Symex]

builtins: dict[str, SBuiltin] = {}

def builtin_form(name: Optional[str] = None) -> Callable[[SBuiltin], SBuiltin]:
    def decorator(func: SBuiltin) -> SBuiltin:
        builtins[name or func.__name__] = func

        return func

    return decorator

def interpreter() -> Interpreter:
    from symex.interpreters.simple import Simple
    return Simple()

@builtin_form()
def Quote(arg_exprs: Sequence[Symex], env: Environment) -> Symex:
    expr, = arg_exprs
    return expr

@builtin_form()
def Lambda(arg_exprs: Sequence[Symex], env: Environment) -> Symex:
    match arg_exprs:
        case (SList() as params, body):
            closure = make_closure(params, None, body, env)
            return closure
        case _:
            raise ValueError("this isn't a well-formed Lambda expression")

@builtin_form('Function')
def Function_(arg_exprs: Sequence[Symex], env: Environment) -> Symex:
    match arg_exprs:
        case (SAtom() as name, SList() as params, body):
            closure = make_closure(params, name, body, env)
            return closure
        case _:
            raise ValueError("this isn't a well-formed Function expression")

@builtin_form()
def And(arg_exprs: Sequence[Symex], env: Environment) -> Symex:
    result: Symex = SAtom(':true')
    for exp in arg_exprs:
        result = interpreter().eval_in(exp, env)
        if not result:
            return result

    return result

@builtin_form()
def Or(arg_exprs: Sequence[Symex], env: Environment) -> Symex:
    result: Symex = SAtom(':false')
    for exp in arg_exprs:
        result = interpreter().eval_in(exp, env)
        if result:
            return result

    return result

@builtin_form()
def Cond(arg_exprs: Sequence[Symex], env: Environment) -> Symex:
    for pair in arg_exprs:
        match pair:
            case SList((condition, action)):
                pass
            case _:
                raise ValueError("this isn't a well-formed condition")

        if interpreter().eval_in(condition, env):
            return interpreter().eval_in(action, env)

    raise ValueError('none of the conditions were true')

@builtin_form()
def Where(arg_exprs: Sequence[Symex], env: Environment) -> Symex:
    body, *bindings = arg_exprs

    for binding in bindings:
        match binding:
            case SList((SAtom() as name, value_expr)):
                pass
            case _:
                raise ValueError("this isn't a well-formed binding")

        result = interpreter().eval_in(value_expr, env)
        env = env.extend_with([Binding(name, result)])

    return interpreter().eval_in(body, env)
