"""
FIRST and FOLLOW sets for a context-free grammar.

Grammar text format (symbols separated by spaces, one rule per line):

    E  -> T E'
    E' -> + T E' | eps
    T  -> F T'
    ...

- The left side of every rule is a non-terminal.
- Any symbol that never appears on a left side is a terminal.
- "eps", "epsilon" or "ε" (or an empty alternative) means the empty string.
- The first rule's left side is the start symbol (unless you pass start=...).

Run:  python first_follow.py            (built-in demo)
      python first_follow.py grammar.txt
"""
import sys

EPS = "ε"
END = "$"


class Grammar:
    def __init__(self, text, start=None):
        self.productions = []      # list of (lhs, tuple_of_rhs_symbols)
        self.nonterminals = []
        for line in text.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            lhs, rhs = line.split("->")
            lhs = lhs.strip()
            if lhs not in self.nonterminals:
                self.nonterminals.append(lhs)
            for alt in rhs.split("|"):
                symbols = tuple(alt.split())
                if symbols in [(), ("eps",), ("epsilon",), (EPS,)]:
                    symbols = ()
                self.productions.append((lhs, symbols))
        self.start = start or self.nonterminals[0]
        self.terminals = []
        for _, rhs in self.productions:
            for s in rhs:
                if s not in self.nonterminals and s not in self.terminals:
                    self.terminals.append(s)

    def is_nt(self, sym):
        return sym in self.nonterminals

    def __str__(self):
        lines = []
        for i, (lhs, rhs) in enumerate(self.productions):
            lines.append(f"({i}) {lhs} -> {' '.join(rhs) if rhs else EPS}")
        return "\n".join(lines)


def first_of_sequence(seq, first, g):
    """FIRST of a string of grammar symbols (uses already computed FIRST sets)."""
    result = set()
    for s in seq:
        if g.is_nt(s):
            result |= first[s] - {EPS}
            if EPS not in first[s]:
                return result
        else:                       # terminal
            result.add(s)
            return result
    result.add(EPS)                 # every symbol was nullable (or seq empty)
    return result


def compute_first(g):
    first = {nt: set() for nt in g.nonterminals}
    changed = True
    while changed:
        changed = False
        for lhs, rhs in g.productions:
            f = first_of_sequence(rhs, first, g)
            if not f <= first[lhs]:
                first[lhs] |= f
                changed = True
    return first


def compute_follow(g, first):
    follow = {nt: set() for nt in g.nonterminals}
    follow[g.start].add(END)
    changed = True
    while changed:
        changed = False
        for lhs, rhs in g.productions:
            for i, sym in enumerate(rhs):
                if not g.is_nt(sym):
                    continue
                f = first_of_sequence(rhs[i + 1:], first, g)
                add = f - {EPS}
                if EPS in f:                 # everything after sym can vanish
                    add |= follow[lhs]
                if not add <= follow[sym]:
                    follow[sym] |= add
                    changed = True
    return follow


def fmt(s):
    return "{ " + ", ".join(sorted(s)) + " }"


def show(g):
    first = compute_first(g)
    follow = compute_follow(g, first)
    print("Grammar:")
    print(g)
    print("\nFIRST sets:")
    for nt in g.nonterminals:
        print(f"  FIRST({nt}) = {fmt(first[nt])}")
    print("\nFOLLOW sets:")
    for nt in g.nonterminals:
        print(f"  FOLLOW({nt}) = {fmt(follow[nt])}")
    return first, follow


DEMO = """
E  -> T E'
E' -> + T E' | eps
T  -> F T'
T' -> * F T' | eps
F  -> ( E ) | id
"""

if __name__ == "__main__":
    text = open(sys.argv[1]).read() if len(sys.argv) > 1 else DEMO
    show(Grammar(text))
