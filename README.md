This is an implementation of a Lisp-like programming language called Symex.

To try it out, you can run

    python -i -m symex

and then

    laugh = open('examples/laugh.smx').read()
    Symex.rep(laugh)

This will parse, evaluate, and print the Lisp expression in `laugh.smx`, and the result of it should be

    (:ha :ha :ha :ha :ha)

PySymex is fully type-annotated and should typecheck successfully with mypy:

    python -m mypy --disallow-untyped-defs symex