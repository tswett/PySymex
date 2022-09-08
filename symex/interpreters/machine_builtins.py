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

from symex.interpreters.machine_frames import FrameResult, StackFrame
from symex.symex import SAtom, SList, Symex
from symex.types import Binding, Closure, Environment

SBuiltin = Callable[[SList, Environment], FrameResult]

builtins: dict[str, SBuiltin] = {}

def builtin_form(name: Optional[str] = None) -> Callable[[SBuiltin], SBuiltin]:
    def decorator(func: SBuiltin) -> SBuiltin:
        builtins[name or func.__name__] = func

        return func

    return decorator

@builtin_form()
def Quote(arg_exprs: SList, env: Environment) -> FrameResult:
    quoted_expr, = arg_exprs
    return FrameResult(result_expr=quoted_expr)

@builtin_form()
def Lambda(arg_exprs: SList, env: Environment) -> FrameResult:
    match arg_exprs:
        case SList((SList() as params, body)):
            closure = Closure.from_defining_parts(params, None, body, env)
            return FrameResult(result_expr=closure.to_symex())
        case _:
            raise ValueError("this isn't a well-formed Lambda expression")

@builtin_form('Function')
def Function_(arg_exprs: SList, env: Environment) -> FrameResult:
    match arg_exprs:
        case SList((SAtom() as name, SList() as params, body)):
            closure = Closure.from_defining_parts(params, name, body, env)
            return FrameResult(result_expr=closure.to_symex())
        case _:
            raise ValueError("this isn't a well-formed Function expression")

@builtin_form('Cond')
def Cond_(arg_exprs: SList, env: Environment) -> FrameResult:
    def assert_list(symex: Symex) -> SList:
        if isinstance(symex, SList):
            return symex
        else:
            raise ValueError("this Cond condition isn't a list")

    case_lists = [assert_list(case) for case in arg_exprs]
    new_frames = [Cond(case_lists, env)]
    return FrameResult(new_frames=new_frames)

class Cond(StackFrame):
    def __init__(self, cases: Sequence[SList], env: Environment):
        self.cases = cases
        self.env = env

    def call(self, _: Optional[Symex]) -> FrameResult:
        from symex.interpreters.machine import Evaluate

        if len(self.cases) == 0:
            raise ValueError('none of the conditions were true')

        first_case, *remaining_cases = self.cases
        condition, outcome = first_case
        new_frames = [GotValueForCond(outcome, remaining_cases, self.env),
                      Evaluate(condition, self.env)]
        return FrameResult(new_frames=new_frames)

class GotValueForCond(StackFrame):
    def __init__(self, outcome_if_true: Symex, remaining_cases: Sequence[SList], env: Environment):
        self.outcome_if_true = outcome_if_true
        self.remaining_cases = remaining_cases
        self.env = env

    def call(self, condition_value: Optional[Symex]) -> FrameResult:
        from symex.interpreters.machine import Evaluate

        if condition_value is None:
            raise ValueError("GotValueForCond didn't get a result")
        if condition_value:
            new_frames: list[StackFrame] = [Evaluate(self.outcome_if_true, self.env)]
        else:
            new_frames = [Cond(self.remaining_cases, self.env)]
        return FrameResult(new_frames=new_frames)

@builtin_form('Where')
def Where_(arg_exprs: SList, env: Environment) -> FrameResult:
    body_expr, *binding_exprs = arg_exprs
    new_frames: list[StackFrame] = [Where(body_expr, binding_exprs, env)]
    return FrameResult(new_frames=new_frames)

class Where(StackFrame):
    def __init__(self, body_expr: Symex, binding_exprs: Sequence[Symex], env: Environment):
        self.body_expr = body_expr
        self.binding_exprs = binding_exprs
        self.env = env

    def call(self, _: Optional[Symex]) -> FrameResult:
        from symex.interpreters.machine import Evaluate

        match self.binding_exprs:
            case ():
                new_frames: list[StackFrame] = [Evaluate(self.body_expr, self.env)]
                return FrameResult(new_frames=new_frames)

            case (SList((SAtom() as name, value_expr)), *remaining_binding_exprs):
                new_frames = [GotValueForWhere(self.body_expr,
                                               remaining_binding_exprs,
                                               self.env,
                                               name),
                              Evaluate(value_expr, self.env)]
                return FrameResult(new_frames=new_frames)

            case _:
                raise ValueError('not a well-formed Where expression')

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
