import re

with open("frontend/static/js/app.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

stack = []
in_template = False
in_single = False
in_double = False
in_line_comment = False
in_block_comment = False

errors = []

for line_no, line in enumerate(lines, 1):
    i = 0
    in_line_comment = False
    while i < len(line):
        c = line[i]
        nxt = line[i+1] if i + 1 < len(line) else ""
        prev = line[i-1] if i > 0 else ""

        if in_line_comment:
            break

        if in_block_comment:
            if c == '*' and nxt == '/':
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        if not in_single and not in_double and not in_template:
            if c == '/' and nxt == '/':
                in_line_comment = True
                break
            if c == '/' and nxt == '*':
                in_block_comment = True
                i += 2
                continue

        # Handle strings
        if not in_double and not in_template and c == "'" and prev != '\\':
            in_single = not in_single
            i += 1
            continue
        if not in_single and not in_template and c == '"' and prev != '\\':
            in_double = not in_double
            i += 1
            continue
        if not in_single and not in_double and c == '`' and prev != '\\':
            in_template = not in_template
            i += 1
            continue

        if in_single or in_double:
            i += 1
            continue

        # Inside template literal, ${ starts an expr
        if in_template:
            if c == '$' and nxt == '{' and prev != '\\':
                stack.append(('}', line_no, i))
                i += 2
                continue
            elif c == '}' and stack and stack[-1][0] == '}':
                stack.pop()
                i += 1
                continue
            i += 1
            continue

        # Normal JS code
        if c in '({[':
            match = ')' if c == '(' else ('}' if c == '{' else ']')
            stack.append((match, line_no, i))
        elif c in ')}]':
            if not stack:
                errors.append(f"Unexpected '{c}' at line {line_no}:{i+1}")
            else:
                expected, open_line, open_col = stack.pop()
                if c != expected:
                    errors.append(f"Mismatched '{c}' at line {line_no}:{i+1}, expected '{expected}' opened at line {open_line}:{open_col+1}")
        i += 1

print(f"Total lines: {len(lines)}")
print(f"Unclosed items in stack: {len(stack)}")
for item in stack[-10:]:
    print(f"  Unclosed expected '{item[0]}' opened at line {item[1]}:{item[2]+1}")
for err in errors[:10]:
    print("  Error:", err)
