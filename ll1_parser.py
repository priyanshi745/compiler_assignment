"""
LL(1) predictive parser: builds the parsing table from FIRST/FOLLOW,
reports conflicts, and parses a token list with a stack (printing a trace).

Run:  python ll1_parser.py
"""
from first_follow import Grammar, compute_first, compute_follow, first_of_sequence, EPS, END, DEMO


def build_ll1_table(g):
    first = compute_first(g)
    follow = compute_follow(g, first)
    table, conflicts = {}, []
    for idx, (lhs, rhs) in enumerate(g.productions):
        f = first_of_sequence(rhs, first, g)
        targets = f - {EPS}
        if EPS in f:
            targets |= follow[lhs]
        for t in targets:
            if (lhs, t) in table:
                conflicts.append((lhs, t, table[(lhs, t)], idx))
            else:
                table[(lhs, t)] = idx
    return table, conflicts


def print_table(g, table):
    cols = g.terminals + [END]
    w = 14
    print("".ljust(6) + "".join(c.ljust(w) for c in cols))
    for nt in g.nonterminals:
        row = nt.ljust(6)
        for c in cols:
            idx = table.get((nt, c))
            cell = ""
            if idx is not None:
                lhs, rhs = g.productions[idx]
                cell = f"{lhs}->{' '.join(rhs) or EPS}"
            row += cell.ljust(w)
        print(row)


def ll1_parse(g, table, tokens, verbose=True):
    stack = [END, g.start]
    tokens = list(tokens) + [END]
    i = 0
    rows = []
    ok = False
    while True:
        top, a = stack[-1], tokens[i]
        stk, rest = " ".join(stack), " ".join(tokens[i:])
        if top == END and a == END:
            rows.append((stk, rest, "accept"))
            ok = True
            break
        if g.is_nt(top):
            idx = table.get((top, a))
            if idx is None:
                rows.append((stk, rest, f"ERROR: no rule for ({top}, {a})"))
                break
            lhs, rhs = g.productions[idx]
            stack.pop()
            stack.extend(reversed(rhs))
            rows.append((stk, rest, f"{lhs} -> {' '.join(rhs) or EPS}"))
        elif top == a:
            stack.pop()
            i += 1
            rows.append((stk, rest, f"match {a}"))
        else:
            rows.append((stk, rest, f"ERROR: expected {top}, got {a}"))
            break
    if verbose:
        print(f"{'STACK':32}{'INPUT':28}ACTION")
        for r in rows:
            print(f"{r[0]:32}{r[1]:28}{r[2]}")
    return ok


if __name__ == "__main__":
    g = Grammar(DEMO)
    table, conflicts = build_ll1_table(g)
    print("LL(1) table:")
    print_table(g, table)
    print("\nConflicts:", conflicts or "none (grammar is LL(1))")
    print("\nParsing: id + id * id")
    print("Accepted:", ll1_parse(g, table, "id + id * id".split()))
    print("\nParsing: id + * id")
    print("Accepted:", ll1_parse(g, table, "id + * id".split()))
