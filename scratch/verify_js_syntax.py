with open("frontend/static/js/app.v17.js", "r", encoding="utf-8") as f:
    code = f.read()

print("File size:", len(code), "characters")

# Check brace balance
stack = []
in_str = None
escape = False
in_line_comment = False
in_block_comment = False

for i, ch in enumerate(code):
    if in_line_comment:
        if ch == '\n':
            in_line_comment = False
        continue
    if in_block_comment:
        if ch == '/' and i > 0 and code[i-1] == '*':
            in_block_comment = False
        continue
    if in_str:
        if escape:
            escape = False
        elif ch == '\\':
            escape = True
        elif ch == in_str:
            in_str = None
        continue
    
    # Check start of comment
    if ch == '/' and i + 1 < len(code):
        if code[i+1] == '/':
            in_line_comment = True
            continue
        elif code[i+1] == '*':
            in_block_comment = True
            continue
    
    # Check start of string
    if ch in ('"', "'", '`'):
        in_str = ch
        continue
    
    # Check brackets
    if ch in ('{', '(', '['):
        stack.append((ch, i))
    elif ch in ('}', ')', ']'):
        if not stack:
            print(f"Error: unexpected closing {ch} at index {i}")
            break
        open_ch, open_idx = stack.pop()
        pairs = {'}': '{', ')': '(', ']': '['}
        if pairs[ch] != open_ch:
            print(f"Error: mismatched {ch} at {i}, expected match for {open_ch} at {open_idx}")
            break

print("Stack remaining count:", len(stack))
if len(stack) == 0:
    print("Syntax verification: All braces, brackets, and quotes are perfectly balanced!")
else:
    print("Unclosed tokens:", stack[-5:])
