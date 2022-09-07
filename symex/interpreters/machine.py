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
from symex.interpreters import Interpreter
from symex.primitives import Primitive
from symex.symex import SAtom, SList
from symex.types import Binding, Closure, Environment, Function

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
        elif head == SAtom('Where'):
            _, body_expr, *binding_exprs = self.expr.as_list
            new_frames: list[StackFrame] = [Where(body_expr, binding_exprs, self.env)]
            return FrameResult(new_frames=new_frames)
        elif head == SAtom('Function'):
            _, name, params, body = self.expr.as_list
            closure = make_closure(name, params, body, self.env)
            return FrameResult(result_expr=closure)
        elif head == SAtom('Lambda'):
            _, params, body = self.expr.as_list
            closure = make_closure(None, params, body, self.env)
            return FrameResult(result_expr=closure)
        elif head == SAtom('Cond'):
            _, *cases = self.expr.as_list
            case_lists = [case.as_list for case in cases]
            new_frames = [Cond(case_lists, self.env)]
            return FrameResult(new_frames=new_frames)
        else:
            new_frames = [EvaluateForCall(self.expr.as_list, [], self.env)]
            return FrameResult(new_frames=new_frames)

def atom_value(expr: Symex, env: Environment) -> Symex:
    if expr.is_data_atom:
        return expr
    else:
        result = env[expr.as_atom]
        return result

def make_closure(name: Optional[Symex], params: Symex, body: Symex, env: Environment) -> Symex:
    if name is None:
        name_list = SList([])
    else:
        if name.is_atom:
            name_list = SList([name])
        else:
            raise ValueError('function name should be an atom')

    if not params.is_list:
        raise ValueError('argument list should be a list')
    params_atoms = SList([param.as_atom for param in params.as_list])

    return SList([SAtom(':closure'),
                    name_list,
                    params_atoms,
                    body,
                    env.to_symex()])

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

            if isinstance(func, Primitive):
                result = func.apply(args)
                return FrameResult(result_expr=result)
            elif isinstance(func, Closure):
                func_env = func.build_env(args)
                new_frames = [Evaluate(func.body, func_env)]
                return FrameResult(new_frames=new_frames)
            else:
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

class Where(StackFrame):
    def __init__(self, body_expr: Symex, binding_exprs: Sequence[Symex], env: Environment):
        self.body_expr = body_expr
        self.binding_exprs = binding_exprs
        self.env = env

    def call(self, _: Optional[Symex]) -> FrameResult:
        if len(self.binding_exprs) == 0:
            new_frames: list[StackFrame] = [Evaluate(self.body_expr, self.env)]
            return FrameResult(new_frames=new_frames)
        else:
            first_binding_expr, *remaining_binding_exprs = self.binding_exprs
            name, value_expr = first_binding_expr.as_list
            name = name.as_atom
            new_frames = [GotValueForWhere(self.body_expr,
                                           remaining_binding_exprs,
                                           self.env,
                                           name),
                          Evaluate(value_expr, self.env)]
            return FrameResult(new_frames=new_frames)

class GotValueForWhere(StackFrame):
    def __init__(self,
                 body_expr: Symex,
                 binding_exprs: Sequence[Symex],
                 env: Environment,
                 new_binding_name: SAtom):
        self.body_expr = body_expr
        self.binding_exprs = binding_exprs
        self.env = env
        self.new_binding_name = new_binding_name

    def call(self, new_value: Optional[Symex]) -> FrameResult:
        if new_value is None:
            raise ValueError("GotValueForWhere didn't get a result")
        else:
            new_binding = Binding(self.new_binding_name, new_value)
            new_env = self.env.extend_with([new_binding])
            new_frames = [Where(self.body_expr, self.binding_exprs, new_env)]
            return FrameResult(new_frames=new_frames)

class Cond(StackFrame):
    def __init__(self, cases: Sequence[SList], env: Environment):
        self.cases = cases
        self.env = env

    def call(self, _: Optional[Symex]) -> FrameResult:
        if len(self.cases) == 0:
            raise ValueError('none of the conditions were true')

        first_case, *remaining_cases = self.cases
        condition, outcome = first_case.as_list
        new_frames = [GotValueForCond(outcome, remaining_cases, self.env),
                      Evaluate(condition, self.env)]
        return FrameResult(new_frames=new_frames)

class GotValueForCond(StackFrame):
    def __init__(self, outcome_if_true: Symex, remaining_cases: Sequence[SList], env: Environment):
        self.outcome_if_true = outcome_if_true
        self.remaining_cases = remaining_cases
        self.env = env

    def call(self, condition_value: Optional[Symex]) -> FrameResult:
        if condition_value is None:
            raise ValueError("GotValueForCond didn't get a result")
        if condition_value:
            new_frames: list[StackFrame] = [Evaluate(self.outcome_if_true, self.env)]
        else:
            new_frames = [Cond(self.remaining_cases, self.env)]
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
