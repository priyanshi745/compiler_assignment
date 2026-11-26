# Shift-Reduce Parser 

grammar = {
    "E": [["E", "+", "E"], ["E", "*", "E"], ["(", "E", ")"], ["id"]],
}

start_symbol = "E"


def shift_reduce_parse(tokens, grammar, start_symbol):
    stack = []
    input_tokens = tokens + ["$"]  # $ marks end of input
    index = 0
    steps = []

    print(f"{'STACK':<30} {'INPUT':<25} ACTION")
    print("-" * 70)

    while True:
        remaining_input = " ".join(input_tokens[index:])
        stack_str = " ".join(stack) if stack else "$"

        reduced = False

        # Try to reduce from the longest possible right-hand side
        for lhs, productions in grammar.items():
            for rhs in productions:
                rhs_len = len(rhs)

                if len(stack) >= rhs_len and stack[-rhs_len:] == rhs:
                    action = f"REDUCE {lhs} -> {' '.join(rhs)}"
                    print(f"{stack_str:<30} {remaining_input:<25} {action}")

                    del stack[-rhs_len:]
                    stack.append(lhs)
                    steps.append(action)
                    reduced = True
                    break

            if reduced:
                break

        if reduced:
            continue

        # Accept condition: stack has only start symbol and input is finished
        if stack == [start_symbol] and input_tokens[index] == "$":
            print(f"{stack_str:<30} {remaining_input:<25} ACCEPT")
            print("\nParsing successful.")
            return True

        # Shift next token
        if input_tokens[index] != "$":
            action = f"SHIFT {input_tokens[index]}"
            print(f"{stack_str:<30} {remaining_input:<25} {action}")

            stack.append(input_tokens[index])
            index += 1
            steps.append(action)
            continue

        # No shift or reduce possible
        print(f"{stack_str:<30} {remaining_input:<25} ERROR")
        print("\nParsing failed.")
        return False


# Example input: id + id * id
tokens = ["id", "+", "id", "*", "id"]

shift_reduce_parse(tokens, grammar, start_symbol)