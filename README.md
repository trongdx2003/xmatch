**xmatch**: Matching two algebraic expressions with Python `ast`

## About

I do this project for fun. 

* The `xm` module provides three functions `shallow_match`, `deep_match`, `many_match`. They parse two algebraic expressions into ASTs and match their left-right components respectively.
* The `thmm` module is still under development. It will provide a class `Theorem` to determine whether a proposition and a theorem mismatch.

It is somewhat useful for verifying natural inequality proofs from Large Language Models (LLMs). Because LLMs could hallucinate, they may produce wrong applications of inequality theorems when manipulating symbols. This tool will provide them feedbacks to refine their proofs (if any mismatches are found).

## Examples

See `xmatch/xm.py` for more details.

```python
from xm import shallow_match, deep_match, many_match

expr1 = "a + b"
expr2 = "x + y"
expr3 = "x ** 2 + y"
expr4 = "z ** 2 + t"

print(deep_match(expr1, expr2))
# {('a', 'x'), ('b', 'y')}

print(shallow_match(expr3, expr4))
# {('x ** 2', 'z ** 2'), ('y', 't')}

print(deep_match(expr3, expr4))
# {('x', 'z'), ('y', 't')}

print(many_match(expr1, expr2))
# [{('a', 'x'), ('b', 'y')}, {('a', 'y'), ('b', 'x')}]
```
