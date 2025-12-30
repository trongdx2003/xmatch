# This module is in development

from xmatch import shallow_match, deep_match

class Theorem:
    def __init__(self, thm: str, match_type: str = "deep", power_as_atomic: bool = True):
        self.thm = thm
        self.match_fun = deep_match if match_type == "deep" else shallow_match
        self.power_as_atomic = power_as_atomic

    def implies(self, expr):
        pass