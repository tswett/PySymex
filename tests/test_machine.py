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

from symex import machine, SAtom, SList, Symex

def test_can_evaluate_quote() -> None:
    input = Symex.parse('(Quote test)')
    result = machine.evaluate(input)

    assert result == SAtom('test')

def test_can_evaluate_tail() -> None:
    input = Symex.parse('(Tail (Quote (test)))')
    result = machine.evaluate(input)

    assert result == SList([])