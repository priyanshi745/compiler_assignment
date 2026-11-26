"""
LALR(1) parser

Builds the LR(1) collection, then merges states that have the same LR(0) core\n(union of lookaheads). Same table size as SLR/LR(0), almost the power of CLR(1).

Self-contained: needs only first_follow.py (Grammar / FIRST / FOLLOW).
Run:  python lalr_parser.py
"""
from first_follow import Grammar, compute_first, first_of_sequence, END, EPS


class LALRParser:
    def __init__(self, text):
        self.g = Grammar(text)
        g = self.g
        self.prods = [(g.start + "'", (g.start,))] + g.productions   # production 0 = augmented
        self.nts = [g.start + "'"] + g.nonterminals
        self.terms = g.terminals + [END]
        self.symbols = g.nonterminals + g.terminals
        self.conflicts = []
        self.action, self.goto = {}, {}
        self.first = compute_first(g)
        self.build()

    # ------------------------------------------- LR(1) items (p, dot, lookahead)
    def closure(self, items):
        closure, work = set(items), list(items)
        while work:
            p, d, la = work.pop()
            rhs = self.prods[p][1]
            if d < len(rhs) and rhs[d] in self.nts:
                f = first_of_sequence(rhs[d + 1:], self.first, self.g)
                lookaheads = (f - {EPS}) | ({la} if EPS in f else set())
                for j, (lhs, _) in enumerate(self.prods):
                    if lhs == rhs[d]:
                        for b in lookaheads:
                            if (j, 0, b) not in closure:
                                closure.add((j, 0, b))
                                work.append((j, 0, b))
        return frozenset(closure)

    def goto_set(self, state, X):
        moved = {(p, d + 1, la) for p, d, la in state
                 if d < len(self.prods[p][1]) and self.prods[p][1][d] == X}
        return self.closure(moved) if moved else None

    def build(self):
        start = self.closure({(0, 0, END)})
        states, trans = self.collection(start)
        self.states, self.trans = self.merge(states, trans)
        self.fill_tables(lambda item: {item[2]})

    @staticmethod
    def merge(states, trans):
        """Merge LR(1) states with identical cores."""
        core = lambda st: frozenset((p, d) for p, d, _ in st)
        new_index, merged, old2new = {}, [], {}
        for i, st in enumerate(states):
            c = core(st)
            if c not in new_index:
                new_index[c] = len(merged)
                merged.append(set())
            merged[new_index[c]] |= st
            old2new[i] = new_index[c]
        new_trans = {(old2new[i], X): old2new[j] for (i, X), j in trans.items()}
        return [frozenset(s) for s in merged], new_trans

    # ---------------------------------------------------- state collection
    def collection(self, start):
        states, index, trans = [start], {start: 0}, {}
        i = 0
        while i < len(states):
            for X in self.symbols:
                nxt = self.goto_set(states[i], X)
                if nxt:
                    if nxt not in index:
                        index[nxt] = len(states)
                        states.append(nxt)
                    trans[(i, X)] = index[nxt]
            i += 1
        return states, trans

    # ------------------------------------------------------------- tables
    def put(self, key, val):
        if key in self.action and self.action[key] != val:
            self.conflicts.append((key[0], key[1], self.action[key], val))
        else:
            self.action[key] = val

    def fill_tables(self, lookaheads):
        for i, st in enumerate(self.states):
            for item in st:
                p, d = item[0], item[1]
                lhs, rhs = self.prods[p]
                if d < len(rhs):
                    if rhs[d] in self.g.terminals:
                        self.put((i, rhs[d]), ("s", self.trans[(i, rhs[d])]))
                elif p == 0:
                    self.put((i, END), ("acc",))
                else:
                    for a in lookaheads(item):
                        self.put((i, a), ("r", p))
        for (i, X), j in self.trans.items():
            if X in self.g.nonterminals:
                self.goto[(i, X)] = j

    # ------------------------------------------------------------ display
    def item_str(self, item):
        p, d = item[0], item[1]
        lhs, rhs = self.prods[p]
        body = list(rhs)
        body.insert(d, "•")
        s = f"{lhs} -> {' '.join(body)}"
        return s + (f" , {item[2]}" if len(item) == 3 else "")

    def print_states(self):
        for i, st in enumerate(self.states):
            print(f"I{i}:")
            for item in sorted(st):
                print("   ", self.item_str(item))

    def print_table(self):
        cols = self.terms + self.g.nonterminals
        print("state".ljust(7) + "".join(c.ljust(7) for c in cols))
        for i in range(len(self.states)):
            row = str(i).ljust(7)
            for c in cols:
                if c in self.terms:
                    a = self.action.get((i, c))
                    cell = "" if not a else "acc" if a[0] == "acc" else f"{a[0]}{a[1]}"
                else:
                    j = self.goto.get((i, c))
                    cell = "" if j is None else str(j)
                row += cell.ljust(7)
            print(row)

    # ------------------------------------------------------------- parser
    def parse(self, tokens, verbose=False):
        """Shift/reduce driver. Returns True if the input is accepted."""
        toks = list(tokens) + [END]
        stack, i = [0], 0
        while True:
            s, a = stack[-1], toks[i]
            act = self.action.get((s, a))
            if verbose:
                shown = "acc" if act and act[0] == "acc" else (f"{act[0]}{act[1]}" if act else "error")
                print(f"{' '.join(map(str, stack)):32} {' '.join(toks[i:]):24} {shown}")
            if act is None:
                return False
            if act[0] == "s":
                stack.append(act[1])
                i += 1
            elif act[0] == "r":
                lhs, rhs = self.prods[act[1]]
                if rhs:
                    del stack[-len(rhs):]
                stack.append(self.goto[(stack[-1], lhs)])
            else:
                return True

    def report(self, label=""):
        print(f"{label}states={len(self.states)}  conflicts={self.conflicts or 'none'}")


EXPR = """
E -> E + T | T
T -> T * F | F
F -> ( E ) | id
"""

NOT_SLR = """
S -> L = R | R
L -> * R | id
R -> L
"""

# LR(1) but not LALR(1): merging creates a reduce/reduce conflict
NOT_LALR = """
S -> a A d | b B d | a B e | b A e
A -> c
B -> c
"""

if __name__ == "__main__":
    p = LALRParser(EXPR)
    print("Expression grammar (12 states for LALR)")
    p.report()
    p.print_table()
    print("\nTrace for: id + id * id")
    print("accepted:", p.parse("id + id * id".split(), verbose=True))

    print("\nNot-SLR grammar is fine for LALR(1):")
    LALRParser(NOT_SLR).report()
    print("\nNot-LALR grammar -> reduce/reduce conflict:")
    LALRParser(NOT_LALR).report()
