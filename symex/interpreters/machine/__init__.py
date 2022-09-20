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

from typing import Optional, Sequence

from symex.interpreters import Interpreter
from symex.interpreters.machine.builtins import builtins
from symex.interpreters.machine.frames import FrameResult, StackFrame
from symex.primitives import Primitive
from symex.symex import SAtom, SList, Symex, slist
from symex.types import Closure, Environment, Function

class Evaluate(StackFrame):
    def __init__(self, expr: Symex, env: Environment):
        self.expr = expr
        self.env = env

    def call(self, _: Optional[Symex]) -> FrameResult:
        match self.expr:
            case SAtom() as atom:
                value = atom_value(atom, self.env)
                return FrameResult(result_expr=value)
            case SList((SAtom(name), *arg_exprs)) if name in builtins:
                return builtins[name](slist(arg_exprs), self.env)
            case SList() as list:
                new_frames = [EvaluateForCall(list, [], self.env)]
                return FrameResult(new_frames=new_frames)
            case _:
                raise ValueError('unknown type of symex')

        raise ValueError('no pattern matched')

def atom_value(expr: SAtom, env: Environment) -> Symex:
    if expr.is_data_atom:
        return expr
    else:
        result = env[expr]
        return result

class EvaluateForCall(StackFrame):
    def __init__(self, expr: SList, values: Sequence[Symex], env: Environment):
        self.expr = expr
        self.values = values
        self.env = env

    def call(self, _: Optional[Symex]) -> FrameResult:
        if len(self.values) < len(self.expr):
            next_expr = self.expr[len(self.values)]
            new_frames = [GotValueForCall(self.expr, self.values, self.env),
                          Evaluate(next_expr, self.env)]
            return FrameResult(new_frames=new_frames)
        else:
            func_expr, *args = self.values
            func = Function.from_symex(func_expr)

            match func:
                case Primitive():
                    result = func.apply(args)
                    return FrameResult(result_expr=result)
                case Closure():
                    func_env = func.build_env(args)
                    new_frames = [Evaluate(func.body, func_env)]
                    return FrameResult(new_frames=new_frames)
                case _:
                    raise ValueError('unknown type of function')

class GotValueForCall(StackFrame):
    def __init__(self, expr: SList, values: Sequence[Symex], env: Environment):
        self.expr = expr
        self.values = values
        self.env = env

    def call(self, new_value: Optional[Symex]) -> FrameResult:
        if new_value is None:
            raise ValueError("GotValueForCall didn't get a result")
        else:
            new_frames = [EvaluateForCall(self.expr, tuple(self.values) + (new_value,), self.env)]
            return FrameResult(new_frames=new_frames)

class Machine(Interpreter):
    def eval_in(self, expr: Symex, env: Environment) -> Symex:
        last_result: Optional[Symex] = None
        call_stack: list[StackFrame] = [Evaluate(expr, env)]

        while call_stack != []:
            top_frame = call_stack.pop()
            frame_result = top_frame.call(last_result)

            call_stack.extend(frame_result.new_frames)
            last_result = frame_result.result_expr

        if last_result is None:
            raise ValueError("the last stack frame didn't return a result")
        else:
            return last_result
