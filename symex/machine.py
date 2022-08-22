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

from typing import Optional, Tuple

from symex import Symex
from symex.symex import Binding, Environment, SAtom

class StackFrame:
    def call(self, expr: Symex) -> Tuple[list[StackFrame], Symex]:
        raise NotImplementedError()

class Evaluate(StackFrame):
    def __init__(self, env: Optional[Environment] = None):
        self.env = env or Environment()

    def call(self, expr: Symex) -> Tuple[list[StackFrame], Symex]:
        if expr.is_atom:
            if expr.is_data_atom:
                return [], expr
            else:
                result = self.env[expr.as_atom]
                return [], result

        head = expr.as_list[0]

        if head == SAtom('Quote'):
            _, quoted_expr = expr.as_list
            return [], quoted_expr
        elif head == SAtom('Tail'):
            # TODO: Sooner or later, this should be implemented as a builtin
            # function, not as a special case.
            _, arg_expr = expr.as_list
            return [Tail(), Evaluate()], arg_expr
        elif head == SAtom('Where'):
            _, arg_expr, *binding_lists = expr.as_list
            bindings = [Binding.from_symex(b) for b in binding_lists]
            new_env = self.env.extend_with(bindings)
            return [Evaluate(new_env)], arg_expr
        else:
            raise ValueError("don't know how to evaluate this list")

class Tail(StackFrame):
    def call(self, expr: Symex) -> Tuple[list[StackFrame], Symex]:
        result = expr.as_list[1:]
        return [], result

def evaluate(expr: Symex) -> Symex:
    current_expr = expr
    call_stack: list[StackFrame] = [Evaluate()]

    while call_stack != []:
        top_frame = call_stack.pop()
        new_frames, current_expr = top_frame.call(current_expr)
        call_stack.extend(new_frames)

    return current_expr