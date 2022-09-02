from . import *

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('filename', nargs='?')

args = parser.parse_args()

if args.filename:
    print(eval_file(args.filename))
