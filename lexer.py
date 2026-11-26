"""
Lexical analyzer (scanner).

 - Regex-based tokenizer with line/column tracking and error reporting
 - Symbol table for identifiers
 - A small hand-built DFA (numbers) to show what a regex becomes underneath

Run:  python lexer.py
"""
import re
from dataclasses import dataclass

KEYWORDS = {"if", "else", "while", "for", "return", "int", "float", "def", "print"}

# Order matters: earlier patterns win (e.g. FLOAT before INT, "==" before "=").
TOKEN_SPEC = [
    ("COMMENT",  r"//[^\n]*|/\*.*?\*/"),
    ("WS",       r"[ \t\r]+"),
    ("NEWLINE",  r"\n"),
    ("FLOAT",    r"\d+\.\d+(?:[eE][+-]?\d+)?"),
    ("INT",      r"\d+"),
    ("STRING",   r'"(?:\\.|[^"\\])*"'),
    ("ID",       r"[A-Za-z_]\w*"),
    ("OP",       r"==|!=|<=|>=|&&|\|\||[+\-*/%=<>!^]"),
    ("DELIM",    r"[(){}\[\];,]"),
    ("MISMATCH", r"."),
]
MASTER = re.compile("|".join(f"(?P<{n}>{p})" for n, p in TOKEN_SPEC), re.S)


@dataclass
class Token:
    type: str
    value: str
    line: int
    col: int

    def __repr__(self):
        return f"<{self.type}, {self.value!r}> @ {self.line}:{self.col}"


class LexError(Exception):
    pass


def tokenize(code, keep_trivia=False):
    """Yield Tokens. Whitespace/comments are skipped unless keep_trivia=True."""
    line, line_start = 1, 0
    for m in MASTER.finditer(code):
        kind, text = m.lastgroup, m.group()
        col = m.start() - line_start + 1
        if kind == "MISMATCH":
            raise LexError(f"Unexpected character {text!r} at {line}:{col}")
        if kind == "ID" and text in KEYWORDS:
            kind = "KEYWORD"
        yield_it = keep_trivia or kind not in ("WS", "NEWLINE", "COMMENT")
        if yield_it:
            yield Token(kind, text, line, col)
        # update line counters (newlines can hide inside block comments)
        nl = text.count("\n")
        if nl:
            line += nl
            line_start = m.start() + text.rfind("\n") + 1


def build_symbol_table(tokens):
    table = {}
    for t in tokens:
        if t.type == "ID":
            e = table.setdefault(t.value, {"first_seen": (t.line, t.col), "count": 0})
            e["count"] += 1
    return table


# ---------------------------------------------------------------- DFA demo
class DFA:
    """Deterministic finite automaton: transitions[(state, char_class)] -> state."""

    def __init__(self, transitions, start, accepting, classify):
        self.t, self.start, self.acc, self.classify = transitions, start, accepting, classify

    def accepts(self, s):
        state = self.start
        for ch in s:
            state = self.t.get((state, self.classify(ch)))
            if state is None:
                return False
        return state in self.acc


def _cls(ch):
    return "digit" if ch.isdigit() else "dot" if ch == "." else "other"


# digits+ ( . digits+ )?     states: 0 start, 1 int, 2 after '.', 3 fraction
NUMBER_DFA = DFA(
    {(0, "digit"): 1, (1, "digit"): 1, (1, "dot"): 2, (2, "digit"): 3, (3, "digit"): 3},
    start=0, accepting={1, 3}, classify=_cls,
)

SAMPLE = '''int x = 42;
float y = 3.14 * (x + 7);   // a comment
/* block
   comment */
if (x >= 10 && y != 0) print("hello\\n");
'''

if __name__ == "__main__":
    print("--- tokens ---")
    toks = list(tokenize(SAMPLE))
    for t in toks:
        print(t)
    print("\n--- symbol table ---")
    for name, info in build_symbol_table(toks).items():
        print(f"{name:6} first seen at {info['first_seen']}, used {info['count']}x")
    print("\n--- DFA for numbers ---")
    for s in ["42", "3.14", "3.", ".5", "1.2.3", "abc"]:
        print(f"{s!r:8} -> {NUMBER_DFA.accepts(s)}")
    print("\n--- error handling ---")
    try:
        list(tokenize("a = 5 @ 3"))
    except LexError as e:
        print("LexError:", e)
