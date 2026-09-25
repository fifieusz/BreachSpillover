import re

with open("frontend/static/js/app.v18.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# Check brace balance
stack = []
in_string = None
in_comment = False
in_template = 0

for line_no, line in enumerate(lines, 1):
    i = 0
    n = len(line)
    while i < n:
        char = line[i]
        
        # Check single-line comment
        if not in_string and i + 1 < n and line[i:i+2] == '//':
            break # rest of line is comment
            
        # Check multi-line comment
        if not in_string and not in_comment and i + 1 < n and line[i:i+2] == '/*':
            in_comment = True
            i += 2
            continue
        if in_comment:
            if i + 1 < n and line[i:i+2] == '*/':
                in_comment = False
                i += 2
            else:
                i += 1
            continue
            
        # Check strings
        if not in_string:
            if char in ('"', "'", '`'):
                in_string = char
                i += 1
                continue
        else:
            if char == '\\':
                i += 2
                continue
            if char == in_string:
                in_string = None
                i += 1
                continue
            i += 1
            continue

        # Check brackets
        if char in ('{', '(', '['):
            stack.append((char, line_no))
        elif char in ('}', ')', ']'):
            expected = {'}': '{', ')': '(', ']': '['}[char]
            if not stack:
                print(f"Error at line {line_no}: unmatched closing '{char}'")
            else:
                top, top_line = stack.pop()
                if top != expected:
                    print(f"Error at line {line_no}: mismatched '{char}', expected match for '{top}' from line {top_line}")
        i += 1

if stack:
    print(f"Unclosed brackets remaining: {len(stack)}")
    for char, l_no in stack[-10:]:
        print(f"  Unclosed '{char}' from line {l_no}")
if in_string:
    print(f"Unclosed string of type {in_string} at end of file!")
if in_comment:
    print(f"Unclosed multi-line comment at end of file!")

print("Check finished.")
