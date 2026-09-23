with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

dark_clash_classes = ['bg-zinc-950', 'border-zinc-800', 'bg-amber-950', 'border-amber-800', 'bg-[#090A0F]', 'text-slate-100', 'text-white']

print("Lines with potential dark clash in index.html:")
for i, line in enumerate(lines):
    if any(c in line for c in dark_clash_classes):
        print(f"Line {i+1}: {line.strip()[:100]}")
