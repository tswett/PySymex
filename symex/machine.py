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

from dataclasses import dataclass, field
from typing import Optional, Sequence

from symex import Symex
# TODO: this shouldn't reference symex.interpreter
from symex.interpreter import Primitive
from symex.symex import Binding, Environment, SAtom, SList

@dataclass(frozen=True)
class FrameResult:
    new_frames: Sequence[StackFrame] = field(default_factory=list)
    result_expr: Optional[Symex] = field(default=None)

class StackFrame:
    def call(self, expr: Optional[Symex]) -> FrameResult:
        raise NotImplementedError()

class Evaluate(StackFrame):
    def __init__(self, expr: Symex, env: Environment):
        self.expr = expr
        self.env = env

    def call(self, _: Optional[Symex]) -> FrameResult:
        if self.expr.is_atom:
            value = atom_value(self.expr, self.env)
            return FrameResult(result_expr=value)

        head = self.expr.as_list[0]

        if head == SAtom('Quote'):
            _, quoted_expr = self.expr.as_list
            return FrameResult(result_expr=quoted_expr)
        else:
            new_frames = [EvaluateForCall(self.expr.as_list, [], self.env)]
            return FrameResult(new_frames=new_frames)

def atom_value(expr: Symex, env: Environment) -> Symex:
    if expr.is_data_atom:
        return expr
    else:
        result = env[expr.as_atom]
        return result

class EvaluateForCall(StackFrame):
    def __init__(self, expr: SList, values: list[Symex], env: Environment):
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
            if is_builtin(self.values[0]):
                result = evaluate_builtin(self.values[0], self.values[1:])
                return FrameResult(result_expr=result)
            else:
                body = get_function_body(self.values[0])
                function_env = build_function_env(self.values[0], self.values[1:])
                new_frames = [Evaluate(body, function_env)]
                return FrameResult(new_frames=new_frames)

class GotValueForCall(StackFrame):
    def __init__(self, expr: SList, values: list[Symex], env: Environment):
        self.expr = expr
        self.values = values
        self.env = env

    def call(self, new_value: Optional[Symex]) -> FrameResult:
        if new_value is None:
            raise ValueError("GotValueForCall didn't get a result")
        else:
            new_frames = [EvaluateForCall(self.expr, self.values + [new_value], self.env)]
            return FrameResult(new_frames=new_frames)

def is_builtin(function: Symex) -> bool:
    return function.is_list and function.as_list[0] == SAtom(':primitive')

def evaluate_builtin(function: Symex, args: list[Symex]) -> Symex:
    builtin = Primitive.from_symex(function)
    return builtin.apply(args)

def get_function_body(function: Symex) -> Symex:
    raise NotImplementedError()

def build_function_env(function: Symex, args: list[Symex]) -> Environment:
    raise NotImplementedError()

def evaluate(expr: Symex, env: Optional[Environment] = None) -> Symex:
    env = env or Primitive.env

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