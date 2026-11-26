"""
Recursive-descent (top-down) parser that builds an AST and evaluates it.
Uses the tokenizer from lexer.py.

Grammar (left recursion removed, precedence encoded in the levels):

    expr    -> term   { ('+' | '-') term }
    term    -> power  { ('*' | '/') power }
    power   -> unary  [ '^' power ]            (right associative)
    unary   -> '-' unary | primary
    primary -> NUMBER | ID | '(' expr ')'

Run:  python recursive_descent.py
"""
from lexer import tokenize, Token


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, text):
        self.toks = list(tokenize(text))
        self.pos = 0

    # --- helpers
    def peek(self):
        return self.toks[self.pos] if self.pos < len(self.toks) else Token("EOF", "", 0, 0)

    def advance(self):
        t = self.peek()
        self.pos += 1
        return t

    def match(self, *values):
        if self.peek().value in values and self.peek().type in ("OP", "DELIM"):
            return self.advance()
        return None

    def expect(self, value):
        t = self.match(value)
        if not t:
            raise ParseError(f"Expected {value!r} but found {self.peek().value!r}")
        return t

    # --- grammar rules
    def parse(self):
        node = self.expr()
        if self.peek().type != "EOF":
            raise ParseError(f"Unexpected token {self.peek().value!r}")
        return node

    def expr(self):
        node = self.term()
        while (op := self.match("+", "-")):
            node = (op.value, node, self.term())
        return node

    def term(self):
        node = self.power()
        while (op := self.match("*", "/")):
            node = (op.value, node, self.power())
        return node

    def power(self):
        node = self.unary()
        if self.match("^"):
            return ("^", node, self.power())
        return node

    def unary(self):
        if self.match("-"):
            return ("neg", self.unary())
        return self.primary()

    def primary(self):
        t = self.peek()
        if t.type in ("INT", "FLOAT"):
            self.advance()
            return ("num", float(t.value) if t.type == "FLOAT" else int(t.value))
        if t.type == "ID":
            self.advance()
            return ("var", t.value)
        if self.match("("):
            node = self.expr()
            self.expect(")")
            return node
        raise ParseError(f"Unexpected token {t.value!r}")


def evaluate(node, env=None):
    env = env or {}
    kind = node[0]
    if kind == "num":
        return node[1]
    if kind == "var":
        return env[node[1]]
    if kind == "neg":
        return -evaluate(node[1], env)
    a, b = evaluate(node[1], env), evaluate(node[2], env)
    return {"+": a + b, "-": a - b, "*": a * b, "/": a / b if b else float("inf"),
            "^": a ** b}[kind]


if __name__ == "__main__":
    for src in ["1 + 2 * 3", "(1 + 2) * 3", "2 ^ 3 ^ 2", "-x + 10 / 4", "2 * (3 + "]:
        try:
            ast = Parser(src).parse()
            print(f"{src:14} AST={ast}  value={evaluate(ast, {'x': 5})}")
        except Exception as e:
            print(f"{src:14} error: {e}")
