import ast
from itertools import permutations, product
from typing import List, Set, Tuple, Any


COMMUTATIVE_OPS = (ast.Add, ast.Mult)

def shallow_match(expr1: str, expr2: str, power_as_atomic: bool = True):
    """Parsing two algebraic expressions into ASTs and matches their left-right components respectively.
    Two binary expressions are matched iff they share the same operators (ast.Pow is handled in some special cases based on the 'power_as_atomic' argument).
    Args:
        expr1 (str): algebraic expression
        expr2 (str): algebraic expression
        power_as_atomic (bool, optional): whether to treat powers as ast.Name instances
    Usage:
    # >>> shallow_match("a+b", "x+y")
    # {('a', 'x'), ('b', 'y')}
    # >>> shallow_match("a**2+b", "x**2+y")
    # {('a ** 2', 'x ** 2'), ('b', 'y')}
    # >>> shallow_match("a**2 + b**2 + c", "x**2+y")
    # {('c', 'y'), ('a ** 2 + b ** 2', 'x ** 2')}
    # >>> shallow_match("a**2 + b**2 + c", "x**2+y", power_as_atomic=False)
    # set()
    # >>> shallow_match("a+b", "x-y") # Two operators are different
    # set()
    """
    try:
        t1 = ast.parse(expr1, mode="eval").body
        t2 = ast.parse(expr2, mode="eval").body
    except SyntaxError:
        return set()

    if not isinstance(t1, ast.BinOp) or not isinstance(t2, ast.BinOp):
        return {(expr1, expr2)}

    if type(t1.op) is not type(t2.op):
        if power_as_atomic:
            if isinstance(t1.op, ast.Pow) or isinstance(t2.op, ast.Pow):
                return {(expr1, expr2)}
        else:
            return set()

    stack = [(t1, t2)]
    results = set()

    while stack:
        x, y = stack.pop()

        if isinstance(x, ast.BinOp) and isinstance(y, ast.BinOp):
            op_x = x.op
            op_y = y.op

            if type(op_x) is not type(op_y):
                if not isinstance(op_x, ast.Pow) and not isinstance(op_y, ast.Pow) or not power_as_atomic:
                    return set()
                results.add((ast.unparse(x), ast.unparse(y)))
                continue

            if isinstance(op_x, ast.Pow):
                if power_as_atomic:
                    results.add((ast.unparse(x), ast.unparse(y)))
                else:
                    stack.extend([(x.right, y.right), (x.left, y.left)])
            else:
                stack.extend([(x.right, y.right), (x.left, y.left)])
        else:
            if isinstance(x, ast.Constant) and isinstance(y, ast.Constant) and x.value == y.value and results:
                continue
            if not power_as_atomic:
                return set()
            results.add((ast.unparse(x), ast.unparse(y)))

    return results


def deep_match(expr1: str, expr2: str, power_as_atomic: bool = True):
    """It works very similar to 'shallow_match' but differs in matching two powers.
    Specifically, matching two powers a**b and c**d yields (a, c) if b = d and (b, d) if a = c, not entire terms.
    This functions will be extended to matching functions.
    Args:
        expr1 (str): algebraic expression
        expr2 (str): algebraic expression
        power_as_atomic (bool, optional): whether to treat powers like ast.Name instances
    Usage:
    # >>> shallow_match("a**2", "x**2")
    # {('a **2', 'x ** 2')}
    # >>> deep_match("a**2", "x**2")
    # {('a', 'x')}
    # >>> deep_match("a**2 + b", "x**2 + y")
    # {('b', 'y'), ('a', 'x')}
    """
    try:
        t1 = ast.parse(expr1, mode="eval").body
        t2 = ast.parse(expr2, mode="eval").body
    except SyntaxError:
        return set()

    if not isinstance(t1, ast.BinOp) or not isinstance(t2, ast.BinOp):
        return {(expr1, expr2)}

    if type(t1.op) is not type(t2.op):
        if power_as_atomic:
            if isinstance(t1.op, ast.Pow) or isinstance(t2.op, ast.Pow):
                return {(expr1, expr2)}
        else:
            return set()

    stack = [(t1, t2)]
    results = set()

    while stack:
        x, y = stack.pop()

        if isinstance(x, ast.BinOp) and isinstance(y, ast.BinOp):
            op_x = x.op
            op_y = y.op

            if type(op_x) is not type(op_y):
                if not isinstance(op_x, ast.Pow) and not isinstance(op_y, ast.Pow) or not power_as_atomic:
                    return set()
                results.add((ast.unparse(x), ast.unparse(y)))
                continue

            if isinstance(op_x, ast.Pow):
                if power_as_atomic:
                    if not isinstance(op_y, ast.Pow):
                        results.add((ast.unparse(x), ast.unparse(y)))
                    else:
                        x_base, x_pow = ast.unparse(x.left), ast.unparse(x.right)
                        y_base, y_pow = ast.unparse(y.left), ast.unparse(y.right)

                        if x_base == y_base:
                            if x_pow != y_pow and (x_pow, y_pow) not in results:
                                results.add((x_pow, y_pow))
                        else:
                            if x_pow == y_pow and (x_base, y_base) not in results:
                                results.add((x_base, y_base))
                            else:
                                results.add((ast.unparse(x), ast.unparse(y)))
                else:
                    stack.extend([(x.right, y.right), (x.left, y.left)])
            else:
                stack.extend([(x.right, y.right), (x.left, y.left)])
        else:
            if isinstance(x, ast.Constant) and isinstance(y, ast.Constant) and x.value == y.value and results:
                continue
            if not power_as_atomic:
                return set()
            results.add((ast.unparse(x), ast.unparse(y)))

    return results


def _reconstruct_left_assoc(operands: List[ast.AST], op_cls: type) -> ast.AST:
    """Reconstruct a left-associative binary tree from operands with operator class op_cls."""
    if not operands:
        raise ValueError("no operands to reconstruct")
    if len(operands) == 1:
        return operands[0]
    cur = ast.BinOp(left=operands[0], op=op_cls(), right=operands[1])
    for opnd in operands[2:]:
        cur = ast.BinOp(left=cur, op=op_cls(), right=opnd)
    return cur


def _flatten_same_op(node: ast.BinOp, op_cls: type) -> List[ast.AST]:
    """Flatten a tree of the same binary operator (associativity).
    Example: (a + (b + c)) -> [a, b, c] when op_cls is ast.Add.
    """
    res = []

    def _collect(n: ast.AST):
        if isinstance(n, ast.BinOp) and isinstance(n.op, op_cls):
            _collect(n.left)
            _collect(n.right)
        else:
            res.append(n)

    _collect(node)
    return res


def _variants(node: ast.AST, power_as_atomic: bool) -> List[ast.AST]:
    """
    Return a list of AST nodes representing all structually-equivalent forms
    of `node` under associativity/commutativity of + and * (and recursion).
    """
    if not isinstance(node, ast.BinOp):
        return [node]

    if isinstance(node.op, ast.Pow) and power_as_atomic:
        return [node]

    if isinstance(node.op, COMMUTATIVE_OPS):
        op_cls = type(node.op)
        flat_operands = _flatten_same_op(node, op_cls)
        operand_variants_lists = [ _variants(opnd, power_as_atomic) for opnd in flat_operands ]

        results = []
        for chosen_operands in product(*operand_variants_lists):
            perm_seen = set()
            for perm in permutations(chosen_operands):
                try:
                    key = tuple(ast.unparse(p) for p in perm)
                except Exception:
                    key = tuple(ast.dump(p) for p in perm)
                if key in perm_seen:
                    continue
                perm_seen.add(key)
                new_node = _reconstruct_left_assoc(list(perm), op_cls)
                results.append(new_node)

        return results

    left_vars = _variants(node.left, power_as_atomic)
    right_vars = _variants(node.right, power_as_atomic)
    res = []
    for L, R in product(left_vars, right_vars):
        new_node = ast.BinOp(left=L, op=type(node.op)(), right=R)
        res.append(new_node)
    return res


def many_match(expr1: str, expr2: str, power_as_atomic: bool = True, mode: str = "deep") -> List[Set[Tuple[Any, Any]]]:
    """
    Enumerate all valid matchings between expr1 and expr2 by:
      - generating all AST-level variants of expr1 under associativity/commutativity of + and *
      - calling base matcher (deep_match or shallow_match) on each variant vs expr2
      - collecting all non-empty match sets as individual matchings (no merging)

    Returns:
        list[ set[ (lhs, rhs) ] ]  -- each element is one consistent matching
    """
    if mode == "deep":
        matcher = deep_match
    elif mode == "shallow":
        matcher = shallow_match
    else:
        raise ValueError("Mode must be 'deep' or 'shallow'")

    try:
        t1 = ast.parse(expr1, mode="eval").body
    except SyntaxError:
        return []

    variants_nodes = _variants(t1, power_as_atomic)

    results_list = []
    seen = set()

    for v in variants_nodes:
        try:
            v_str = ast.unparse(v)
        except Exception:
            v_str = expr1

        match_set = matcher(v_str, expr2, power_as_atomic)
        if match_set:
            key = frozenset(match_set)
            if key in seen:
                continue
            seen.add(key)
            results_list.append(set(match_set))

    return results_list