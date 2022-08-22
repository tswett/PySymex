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

from typing import Tuple

from symex import Symex
from symex.symex import SAtom

class StackFrame:
    def call(self, expr: Symex) -> Tuple[list[StackFrame], Symex]:
        raise NotImplementedError()

class Evaluate(StackFrame):
    def call(self, expr: Symex) -> Tuple[list[StackFrame], Symex]:
        if expr.is_data_atom:
            return [], expr

        head = expr.as_list[0]

        if head == SAtom('Quote'):
            _, quoted_expr = expr.as_list
            return [], quoted_expr
        elif head == SAtom('Tail'):
            _, arg_expr = expr.as_list
            return [Tail(), Evaluate()], arg_expr
        else:
            raise ValueError("don't know how to evaluate this")

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