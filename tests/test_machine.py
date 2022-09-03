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

from symex import SAtom, SList, Symex
from symex.interpreters.machine import Machine

def test_can_evaluate_quote() -> None:
    input = Symex.parse('(Quote test)')
    result = Machine().eval(input)

    assert result == SAtom('test')

def test_can_evaluate_tail() -> None:
    input = Symex.parse('(Tail (Quote (test)))')
    result = Machine().eval(input)

    assert result == SList([])

def test_can_evaluate_data_atom() -> None:
    input = SAtom(':test')
    result = Machine().eval(input)

    assert result == SAtom(':test')

def test_empty_where() -> None:
    input = Symex.parse('(Where :test)')
    result = Machine().eval(input)

    assert result == SAtom(':test')

def test_simple_where() -> None:
    input = Symex.parse('(Where color (color :blue))')
    result = Machine().eval(input)

    assert result == SAtom(':blue')

def test_expression_where() -> None:
    input = Symex.parse('(Where list (list (Head (Quote (test)))))')
    result = Machine().eval(input)

    assert result == SAtom('test')

def test_nested_where() -> None:
    input = Symex.parse('''
        (Where (Where color
                      (flavor :raspberry))
               (color :blue))
    ''')
    result = Machine().eval(input)

    assert result == SAtom(':blue')

def test_hiding_where() -> None:
    input = Symex.parse('''
        (Where (Where color
                      (color :yellow))
               (color :blue))
    ''')
    result = Machine().eval(input)

    assert result == SAtom(':yellow')

def test_simple_function() -> None:
    input = Symex.parse('((Function Test (x f) (f x)) (List :hello) Head)')
    result = Machine().eval(input)

    assert result == SAtom(':hello')

def test_simple_cond() -> None:
    input = Symex.parse('(Cond (:true (Quote test)))')
    result = Machine().eval(input)

    assert result == SAtom('test')

def test_can_evaluate_laugh() -> None:
    input = Symex.parse('''
        (Where (Laugh (List :one :two :three :four :five))
            (Laugh (Function Laugh (list)
                (Cond ((= list (List))
                        (List))
                       (:true
                           (Cons :ha (Laugh (Tail list))))))))
    ''')

    result = Machine().eval(input)

    assert result == Symex.parse('(:ha :ha :ha :ha :ha)')