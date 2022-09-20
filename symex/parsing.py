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

from symex.symex import SAtom, SList, Symex, slist

class SymexParser():
    def __init__(self, text: str):
        self.text: str = text
        self.next_index: int = 0

    @staticmethod
    def parse(text: str) -> Symex:
        parser = SymexParser(text)
        result = parser.parse_with_tail()
        parser.consume_whitespace()

        if parser.next_char is None:
            return result
        else:
            raise ValueError('extra text was present after the end of the expression')

    def parse_with_tail(self) -> Symex:
        self.consume_whitespace()

        if self.next_char is None:
            raise ValueError('unexpected end of input')

        if self.next_char == '(':
            return self.parse_list_with_tail()

        if self.is_atom_char(self.next_char):
            return self.parse_atom_with_tail()

        raise ValueError('failed to find a recognizable character')

    def parse_atom_with_tail(self) -> SAtom:
        self.consume_whitespace()

        result_str = ''

        while (next_char := self.next_char) is not None and self.is_atom_char(next_char):
            result_str += next_char
            self.next_index += 1

        if result_str == '':
            raise ValueError('failed to find an atom character')
        else:
            return SAtom(result_str)

    @staticmethod
    def is_atom_char(char: str) -> bool:
        return char.isalnum() or char in "*+-./:<=>?_"

    def parse_list_with_tail(self) -> SList:
        self.consume_whitespace()

        if self.next_char == '(':
            self.next_index += 1
        else:
            raise ValueError('failed to find an opening parenthesis')

        result_list = []

        self.consume_whitespace()

        while self.next_char != ')':
            item = self.parse_with_tail()
            result_list.append(item)
            self.consume_whitespace()

        if self.next_char == ')':
            self.next_index += 1
            return slist(result_list)
        else:
            raise ValueError('failed to find a closing parenthesis')

    def consume_whitespace(self) -> None:
        while ((next_char := self.next_char) is not None and
               (next_char.isspace() or next_char == ';')):
            if self.next_char == ';':
                while self.next_char != '\n' and self.next_char is not None:
                    self.next_index += 1
            else:
                self.next_index += 1

    @property
    def next_char(self) -> Optional[str]:
        if self.next_index == len(self.text):
            return None
        else:
            return self.text[self.next_index]
