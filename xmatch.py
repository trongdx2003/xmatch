import ast


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
            results.add((ast.unparse(x), ast.unparse(y)))

    return results