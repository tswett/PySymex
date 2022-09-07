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

from typing import Sequence
from symex.primitives import Primitive
from symex.symex import SAtom, Symex
from symex.types import Binding, Environment

def is_primitive(function: Symex) -> bool:
    return function.is_list and function.as_list[0] == SAtom(':primitive')

def evaluate_primitive(function: Symex, args: Sequence[Symex]) -> Symex:
    primitive = Primitive.from_symex(function)
    return primitive.apply(args)

def get_function_body(function: Symex) -> Symex:
    _head, _name, _params, body, _env = function.as_list
    return body

def build_function_env(function: Symex, args: Sequence[Symex]) -> Environment:
    _head, name_list, params, _body, env_expr = function.as_list

    params = params.as_list
    env = Environment.from_symex(env_expr)

    if len(args) != len(params):
        raise ValueError('closure got wrong number of arguments')

    bindings = [Binding(param.as_atom, arg) for param, arg in zip(params, args)]

    if len(name_list.as_list) > 0:
        name, = name_list.as_list
        bindings = [Binding(name.as_atom, function)] + bindings

    new_env = env.extend_with(bindings)

    return new_env
