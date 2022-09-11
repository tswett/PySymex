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

"""Interpreters for evaluating Lisp expressions

These are the interpreters—the code responsible for actually evaluating an
expression to obtain a value.

Currently, there are two interpreters:

* `symex.interpreters.simple` is a relatively simple interpreter.
* `symex.interpreters.machine` is a more complicated interpreter that uses an
  explicit call stack.

The advantage of `machine` over `simple` is that `machine` is implemented
non-recursively, and as a result, it uses only a few frames on Python's call
stack, no matter how deep the recursive calls in Lisp go. On the other hand,
`simple` uses a lot of recursive calls, and as a result, it may end up
overflowing the stack even when doing something as simple as mapping a function
over a list containing 1,000 elements.

The `machine` interpreter will probably be abandoned and eventually deleted,
since its design is poor. In particular, it attempts to directly interpret the
syntax tree (which is, of course, recursive) using a non-recursive algorithm. As
a result, the logic is very difficult to follow.

In its place, there's going to be an interpreter which first translates Lisp
expressions into a form that is easy to execute non-recursively, and then
executes that.
"""

from typing import Optional

from symex.primitives import primitive_env
from symex.symex import Symex
from symex.types import Environment

class Interpreter:
    def eval_in(self, expr: Symex, env: Environment) -> Symex:
        raise NotImplementedError()

    def eval(self, expr: Symex, env: Optional[Environment] = None) -> Symex:
        return self.eval_in(expr, env or primitive_env)

    def rep(self, input: str) -> str:
        return str(self.eval(Symex.parse(input)))

    def eval_file(self, filename: str) -> Symex:
        contents = open(filename).read()
        expression = Symex.parse(contents)
        result = self.eval(expression)
        return result
