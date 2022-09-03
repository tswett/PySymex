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
