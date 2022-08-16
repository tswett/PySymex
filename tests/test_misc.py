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

def test_can_parse_an_atom() -> None:
    result = Symex.parse('test')
    assert result == SAtom('test')

def test_can_parse_a_list() -> None:
    result = Symex.parse('(one two)')
    assert result == SList([SAtom('one'), SAtom('two')])

def test_laugh() -> None:
    program = '''
        (Where (Laugh (List :one :two :three :four :five))
            (Laugh (Function Laugh (list)
                (Cond ((= list (List))
                        (List))
                    (:true
                        (Cons :ha (Laugh (Tail list))))))))
    '''

    output = Symex.rep(program)

    assert output == '(:ha :ha :ha :ha :ha)'
