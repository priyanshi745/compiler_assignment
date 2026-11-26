"""
Operator-precedence parsing.

1. Table-driven operator-precedence parser (bottom-up, shift/reduce).
   The precedence relations are  <.  (yields to),  =  (equal),  .>  (takes
   precedence)  between the top terminal on the stack and the next input token.
   The table is generated from a simple list of operator levels.

2. Precedence climbing: the compact recursive version of the same idea.

Grammar handled (ambiguous on purpose; precedence/associativity resolve it):
    E -> E + E | E - E | E * E | E / E | E ^ E | ( E ) | id

Run:  python operator_precedence.py
"""
import re

# (operators, associativity), lowest precedence first
LEVELS = [
    (["+", "-"], "left"),
    (["*", "/"], "left"),
    (["^"], "right"),
]
END = "$"


def build_table(levels=LEVELS):
    prec, assoc = {}, {}
    for level, (ops, a) in enumerate(levels, start=1):
        for op in ops:
            prec[op], assoc[op] = level, a
    ops = list(prec)
    terms = ops + ["id", "(", ")", END]
    table = {}
    for a in terms:
        for b in terms:
            rel = None
            if a == END and b == END:
                rel = "acc"
            elif a == END:
                rel = "<" if b not in (")",) else None
            elif b == END:
                rel = ">" if a != "(" else None
            elif a == "id":
                rel = ">" if b not in ("id", "(") else None
            elif b == "id":
                rel = "<" if a != "id" and a != ")" else None
            elif a == "(":
                rel = "=" if b == ")" else ("<" if b != END else None)
            elif a == ")":
                rel = ">" if b not in ("id", "(") else None
            elif b == "(":
                rel = "<"
            elif b == ")":
                rel = ">"
            else:                                   # both are operators
                if prec[a] > prec[b]:
                    rel = ">"
                elif prec[a] < prec[b]:
                    rel = "<"
                else:
                    rel = ">" if assoc[a] == "left" else "<"
            if rel:
                table[(a, b)] = rel
    return table, terms


def print_table(table, terms):
    print("     " + "".join(t.ljust(5) for t in terms))
    for a in terms:
        print(a.ljust(5) + "".join(table.get((a, b), "·").ljust(5) for b in terms))


def tokenize(text):
    """Numbers and identifiers become terminal 'id' (lexeme kept)."""
    out = []
    for m in re.finditer(r"\s*(\d+(?:\.\d+)?|[A-Za-z_]\w*|[-+*/^()])", text):
        lex = m.group(1)
        out.append(("id" if re.match(r"[\w.]+$", lex) else lex, lex))
    return out


class OPError(Exception):
    pass


def op_parse(text, table=None, verbose=False):
    """Returns an AST (nested tuples). Stack entries: ('T', term, lexeme) or ('N', node)."""
    table = table or build_table()[0]
    toks = tokenize(text) + [(END, END)]
    stack = [("T", END, END)]
    i = 0

    def top_terminal():
        for e in reversed(stack):
            if e[0] == "T":
                return e[1]

    while True:
        a, (b, lex) = top_terminal(), toks[i]
        rel = table.get((a, b))
        if verbose:
            show = " ".join(e[1] if e[0] == "T" else "E" for e in stack)
            print(f"{show:24} {' '.join(t[1] for t in toks[i:]):24} {rel}")
        if rel == "acc":
            if len(stack) == 2 and stack[1][0] == "N":
                return stack[1][1]
            raise OPError("Incomplete expression")
        if rel in ("<", "="):                       # shift
            stack.append(("T", b, lex))
            i += 1
        elif rel == ">":                            # reduce: pop the handle
            handle, last = [], None
            while True:
                sym = stack.pop()
                handle.insert(0, sym)
                if sym[0] == "T":
                    last = sym[1]
                    if table.get((top_terminal(), last)) == "<":
                        if stack and stack[-1][0] == "N":
                            handle.insert(0, stack.pop())
                        break
            stack.append(("N", build_node(handle)))
        else:
            raise OPError(f"Syntax error near {lex!r} (no relation between {a!r} and {b!r})")


def build_node(h):
    kinds = [x[0] for x in h]
    if kinds == ["T"] and h[0][1] == "id":
        return ("id", h[0][2])
    if kinds == ["N", "T", "N"]:
        return (h[1][1], h[0][1], h[2][1])
    if kinds == ["T", "N", "T"] and h[0][1] == "(" and h[2][1] == ")":
        return h[1][1]
    shown = " ".join("E" if x[0] == "N" else x[1] for x in h)
    raise OPError(f"Syntax error: cannot reduce '{shown}' (missing operand or operator?)")


# ------------------------------------------------------- precedence climbing
PREC = {"+": (1, "left"), "-": (1, "left"), "*": (2, "left"), "/": (2, "left"), "^": (3, "right")}


def climb(text):
    toks = [lex for _, lex in tokenize(text)]
    pos = 0

    def parse_expr(min_prec):
        nonlocal pos
        lhs = parse_atom()
        while pos < len(toks) and toks[pos] in PREC and PREC[toks[pos]][0] >= min_prec:
            op = toks[pos]
            p, assoc = PREC[op]
            pos += 1
            rhs = parse_expr(p + 1 if assoc == "left" else p)
            lhs = (op, lhs, rhs)
        return lhs

    def parse_atom():
        nonlocal pos
        if pos >= len(toks):
            raise OPError("Unexpected end of input")
        t = toks[pos]
        pos += 1
        if t == "(":
            node = parse_expr(1)
            if pos >= len(toks) or toks[pos] != ")":
                raise OPError("Missing ')'")
            pos += 1
            return node
        if re.match(r"[\w.]+$", t):
            return ("id", t)
        raise OPError(f"Unexpected token {t!r}")

    node = parse_expr(1)
    if pos != len(toks):
        raise OPError(f"Unexpected token {toks[pos]!r}")
    return node


if __name__ == "__main__":
    table, terms = build_table()
    print("Operator precedence relations (row = stack top, column = input):")
    print_table(table, terms)

    print("\nTrace for: a + b * c")
    op_parse("a + b * c", table, verbose=True)

    print("\nAST comparison (table-driven vs precedence climbing):")
    for src in ["a + b * c", "a - b - c", "2 ^ 3 ^ 2", "(a + b) * c / d"]:
        print(f"{src:18} {op_parse(src, table)}   |   {climb(src)}")

    print()
    for bad in ["a + * b", "a b", "(a + b"]:
        try:
            op_parse(bad, table)
        except OPError as e:
            print(f"{bad!r}: {e}")
