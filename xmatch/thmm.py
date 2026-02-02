import ast
from dataclasses import dataclass
from itertools import product
from xm import shallow_match, deep_match, many_match


@dataclass
class Theorem:
    thm: str

    _MATCHERS = {
        "deep":    (deep_match, False),
        "shallow": (shallow_match, False),
        "many":    (many_match, True),
    }

    _COMPARE_RULES = {
        (ast.Eq, ast.Eq):   ("lhs", "rhs"),

        (ast.GtE, ast.GtE): ("lhs", "rhs"),
        (ast.GtE, ast.LtE): ("rhs", "lhs"),

        (ast.LtE, ast.LtE): ("lhs", "rhs"),
        (ast.LtE, ast.GtE): ("rhs", "lhs"),
    }

    @staticmethod
    def _empty(is_many: bool):
        return [] if is_many else set()

    @staticmethod
    def _concat(left, right, is_many: bool):
        if not is_many:
            return left | right
        return [l | r for l, r in product(left, right)]

    @staticmethod
    def _vars(node: ast.AST) -> set[str]:
        return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}

    @staticmethod
    def _parse_compare(s: str):
        try:
            node = ast.parse(s, mode="eval").body
        except SyntaxError:
            print("Warning: invalid syntax")
            return None

        if not isinstance(node, ast.Compare) or len(node.ops) != 1:
            print("Warning: invalid or chained comparison")
            return None

        return node

    def match(self, expr: str, match_function: str = "deep", power_as_atomic: bool = True, mode_for_many: str = "deep"):
        try:
            matcher, is_many = self._MATCHERS[match_function]
        except KeyError:
            raise ValueError(f"Unsupported matching function: {match_function}")

        t_thm = self._parse_compare(self.thm)
        t_expr = self._parse_compare(expr)
        if not t_thm or not t_expr:
            return self._empty(is_many)

        if self._vars(t_thm) & self._vars(t_expr):
            print("Warning: theorem and expression share variable names")
            return self._empty(is_many)

        op_thm = type(t_thm.ops[0])
        op_expr = type(t_expr.ops[0])

        if op_thm is ast.Eq and op_expr is not ast.Eq:
            return self._empty(is_many)

        if op_thm in (ast.GtE, ast.LtE) and op_expr in (ast.Gt, ast.Lt):
            print("Warning: >= / <= theorem cannot imply strict inequality")
            return self._empty(is_many)

        rule = self._COMPARE_RULES.get((op_thm, op_expr))
        if not rule:
            return self._empty(is_many)

        lhs_thm = ast.unparse(t_thm.left)
        rhs_thm = ast.unparse(t_thm.comparators[0])
        lhs_expr = ast.unparse(t_expr.left)
        rhs_expr = ast.unparse(t_expr.comparators[0])

        def _match(a, b):
            if is_many:
                return many_match(a, b, power_as_atomic, mode_for_many)
            return matcher(a, b, power_as_atomic)

        expr_map = {"lhs": lhs_expr, "rhs": rhs_expr}
        fns_matched = _match(lhs_thm, expr_map[rule[0]])
        snd_matched = _match(rhs_thm, expr_map[rule[1]])
        if fns_matched and snd_matched:
            return self._concat(fns_matched, snd_matched, is_many)
        return self._empty(is_many)

