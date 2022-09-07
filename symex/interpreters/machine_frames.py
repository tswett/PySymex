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

from dataclasses import dataclass, field
from typing import Optional, Sequence

from symex.symex import Symex

@dataclass(frozen=True)
class FrameResult:
    new_frames: Sequence[StackFrame] = field(default_factory=list)
    result_expr: Optional[Symex] = field(default=None)

class StackFrame:
    def call(self, expr: Optional[Symex]) -> FrameResult:
        raise NotImplementedError()
