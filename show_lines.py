
with open('orchestrator.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
print()
print("Lines 300-315:")
for i in range(299, min(315, len(lines))):
    marker = ">>>" if i in [306, 309] else "   "
    print(f"{marker} {i+1:4d}: {repr(lines[i])}")
