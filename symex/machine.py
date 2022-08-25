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

from symex.symex import Environment, SAtom, Symex

EngineAction = None

class ListMachine:
    '''A ListMachine is a finite state machine implementing one stack frame.'''

    def __init__(self, engine: StackEngine, expr: Symex, env: Environment) -> None:
        self.engine = engine
        self.expr = expr
        self.env = env
        self.subexpr_values = []

    def start(self) -> EngineAction:
        if self.expr.is_atom:
            return self.engine.return_(self.expr.eval_in(self.env))
        else:
            return self.engine.continue_to(self.evaluate_subexprs)

    def evaluate_subexprs(self) -> EngineAction:
        value_count = len(self.subexpr_values)
        if value_count == len(self.expr.as_list):
            return self.engine.continue_to(self.apply)
        else:
            next_subexpr = self.expr.as_list[value_count]
            return self.engine.recurse(
                recursion_args=[next_subexpr, self.env],
                continue_callback=self.got_subexpr_value)

    def got_subexpr_value(self, subexpr_value: Symex) -> EngineAction:
        self.subexpr_values.append(subexpr_value)
        return self.engine.continue_to(self.got_subexpr_value)

    def apply(self) -> EngineAction:
        func, *args = self.subexpr_values
        if is_primitive_function(func):
            return self.engine.return_(apply_primitive_function(func, args))
        else:
            body = function_body(func)
            env = environment_for_call(func, args)
            return self.engine.tail_call(body, env)

def is_primitive_function(func: Symex) -> bool:
    return func.is_list and func.as_list[0] == SAtom(':primitive')

def apply_primitive_function(func: Symex, args: list[Symex]) -> Symex:
    raise NotImplementedError()

def function_body(func: Symex) -> Symex:
    raise NotImplementedError()

def environment_for_call(func: Symex, args: list[Symex]) -> Environment:
    raise NotImplementedError()

class StackEngine:
    def __init__(self, machine_factory) -> None:
        self.stack = []
        self.machine_factory = machine_factory

    def execute(self, *args):
        self.start_machine(args)
        current_value = None

        while len(self.stack) != 0:
            callback, args, use_return_value = self.stack.pop()
            if use_return_value:
                current_value = callback(current_value, *args)
            else:
                current_value = callback(*args)

        return current_value

    def start_machine(self, args):
        machine = self.machine_factory(self, *args)
        self.stack.append((machine.start, [], False))

    def return_(self, value):
        return value

    def continue_to(self, callback, *args):
        self.stack.append((callback, args, False))

    def recurse(self, recursion_args, continue_callback, *continue_args):
        self.stack.append((continue_callback, continue_args, True))
        self.start_machine(recursion_args)

    def tail_call(self, *args):
        self.start_machine(args)

def evaluate(expr: Symex) -> Symex:
    return StackEngine(ListMachine).execute(expr, Environment([]))