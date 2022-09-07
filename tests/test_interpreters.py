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

import pytest

from symex import SAtom, SList, Symex
from symex.interpreters import Interpreter
from symex.interpreters.machine import Machine
from symex.interpreters.simple import Simple

@pytest.mark.parametrize('interpreter', [Simple(), Machine()])
class TestInterpreters:
    def test_can_evaluate_quote(self, interpreter: Interpreter) -> None:
        input = Symex.parse('(Quote test)')
        result = interpreter.eval(input)

        assert result == SAtom('test')

    def test_can_evaluate_tail(self, interpreter: Interpreter) -> None:
        input = Symex.parse('(Tail (Quote (test)))')
        result = interpreter.eval(input)

        assert result == SList([])

    def test_can_evaluate_data_atom(self, interpreter: Interpreter) -> None:
        input = SAtom(':test')
        result = interpreter.eval(input)

        assert result == SAtom(':test')

    def test_empty_where(self, interpreter: Interpreter) -> None:
        input = Symex.parse('(Where :test)')
        result = interpreter.eval(input)

        assert result == SAtom(':test')

    def test_simple_where(self, interpreter: Interpreter) -> None:
        input = Symex.parse('(Where color (color :blue))')
        result = interpreter.eval(input)

        assert result == SAtom(':blue')

    def test_expression_where(self, interpreter: Interpreter) -> None:
        input = Symex.parse('(Where list (list (Head (Quote (test)))))')
        result = interpreter.eval(input)

        assert result == SAtom('test')

    def test_nested_where(self, interpreter: Interpreter) -> None:
        input = Symex.parse('''
            (Where (Where color
                        (flavor :raspberry))
                (color :blue))
        ''')
        result = interpreter.eval(input)

        assert result == SAtom(':blue')

    def test_hiding_where(self, interpreter: Interpreter) -> None:
        input = Symex.parse('''
            (Where (Where color
                        (color :yellow))
                (color :blue))
        ''')
        result = interpreter.eval(input)

        assert result == SAtom(':yellow')

    def test_simple_function(self, interpreter: Interpreter) -> None:
        input = Symex.parse('((Function Test (x f) (f x)) (List :hello) Head)')
        result = interpreter.eval(input)

        assert result == SAtom(':hello')

    def test_simple_lambda(self, interpreter: Interpreter) -> None:
        input = Symex.parse('((Lambda (x f) (f x)) (List :hello) Head)')
        result = interpreter.eval(input)

        assert result == SAtom(':hello')

    def test_simple_cond(self, interpreter: Interpreter) -> None:
        input = Symex.parse('(Cond (:true (Quote test)))')
        result = interpreter.eval(input)

        assert result == SAtom('test')

    def test_quine(self, interpreter: Interpreter) -> None:
        input = Symex.parse('''
            ((Lambda (expr)
                (List expr
                      (List (Quote Quote) expr)))
            (Quote (Lambda (expr)
                        (List expr
                              (List (Quote Quote) expr)))))
        ''')

        result = interpreter.eval(input)

        assert result == input

    def test_laugh(self, interpreter: Interpreter) -> None:
        input = Symex.parse('''
            (Where (Laugh (List :one :two :three :four :five))
                (Laugh (Function Laugh (list)
                    (Cond ((= list Nil)
                            Nil)
                           (:true
                               (Cons :ha (Laugh (Tail list))))))))
        ''')

        result = interpreter.eval(input)

        assert result == Symex.parse('(:ha :ha :ha :ha :ha)')
