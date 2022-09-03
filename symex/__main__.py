from . import *

import argparse

from symex.interpreters.simple import Simple

parser = argparse.ArgumentParser()
parser.add_argument('filename', nargs='?')

args = parser.parse_args()

if args.filename:
    print(Simple().eval_file(args.filename))
