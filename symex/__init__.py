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

"""This is an experimental implementation of Lisp.

This language is purely functional, and it always will be. So far, there is no
`define` or `def` form, since it's not quite obvious how to implement such a
thing in a purely functional language.

Here's a simple example of this language:

```
(Where (Laugh (List :one :two :three :four :five))
    (Laugh (Function Laugh (list)
        (Cond ((= list Nil)
                  Nil)
              (:true
                  (Cons :ha (Laugh (Tail list))))))))
```

This evaluates to `(:ha :ha :ha :ha :ha)`.

Despite the etymology, "symex" is pronounced /ˈsaɪmɛks/ (sigh-mex).

## Trying it out

The fundamental type is `symex.symex.Symex`, which represents a symbolic
expression (S-expression). You can create a Symex using the Symex.parse method:

```python
from symex.symex import Symex
expr = Symex.parse('(Quote ((here there) (these those)))')
```

In order to find the value of this expression, you need an interpreter. You can
use the Simple interpreter like so:

```python
from symex.interpreters.simple import Simple
interpreter = Simple()
result = interpreter.eval(expr)
```

Now you can view the result by running

```python
str(result)
```

which should return the string `((here there) (these those))`.

## Code architecture

The general organization of the code is:

* `symex.symex` – fundamental data types (S-expressions, lists, and atoms)
* `symex.types` – some more complex types that are used by the interpreters
* `symex.primitives` – some functions which operate on S-expressions, and are exposed
  to the Lisp programmer as primitives
* `symex.parsing` – the parser
* `symex.interpreters` – some interpreters, which actually evaluate expressions
"""

__all__ = ['interpreters', 'parsing', 'primitives', 'symex', 'types']
