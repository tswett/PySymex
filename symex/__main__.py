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

from . import *

import argparse

from symex.interpreters.simple import Simple

parser = argparse.ArgumentParser()
parser.add_argument('filename', nargs='?')

args = parser.parse_args()

if args.filename:
    print(Simple().eval_file(args.filename))
