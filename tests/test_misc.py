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

from symex.symex import SAtom, Symex, slist

def test_can_parse_an_atom() -> None:
    result = Symex.parse('test')
    assert result == SAtom('test')

def test_can_parse_a_list() -> None:
    result = Symex.parse('(one two)')
    assert result == slist([SAtom('one'), SAtom('two')])
