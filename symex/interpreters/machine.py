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
from symex.primitives import Primitive, primitive_env
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
        elif head == SAtom('Where'):
            _, body_expr, *binding_exprs = self.expr.as_list
            new_frames: list[StackFrame] = [Where(body_expr, binding_exprs, self.env)]
            return FrameResult(new_frames=new_frames)
        elif head == SAtom('Function'):
            _, name, params, body = self.expr.as_list
            closure = make_closure(name, params, body, self.env)
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

def make_closure(name: Symex, params: Symex, body: Symex, env: Environment) -> Symex:
    if not name.is_atom:
        raise ValueError('function name should be an atom')
    if not params.is_list:
        raise ValueError('argument list should be a list')
    params_atoms = [param.as_atom for param in params.as_list]

    return SList([SAtom(':closure'),
                    SList([name]),
                    params,
                    body,
                    env.to_symex()])

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

class Where(StackFrame):
    def __init__(self, body_expr: Symex, binding_exprs: list[Symex], env: Environment):
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
                 binding_exprs: list[Symex],
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

def is_builtin(function: Symex) -> bool:
    return function.is_list and function.as_list[0] == SAtom(':primitive')

def evaluate_builtin(function: Symex, args: list[Symex]) -> Symex:
    builtin = Primitive.from_symex(function)
    return builtin.apply(args)

def get_function_body(function: Symex) -> Symex:
    _head, _name, _params, body, _env = function.as_list
    return body

def build_function_env(function: Symex, args: list[Symex]) -> Environment:
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

def evaluate(expr: Symex, env: Optional[Environment] = None) -> Symex:
    env = env or primitive_env

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