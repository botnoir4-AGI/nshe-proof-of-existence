
with open('orchestrator.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Find where successful execution is handled
for i, line in enumerate(lines):
    if 'successful_results' in line or '_update_curriculum' in line or 'store_to_memory' in line:
        print(f"{i+1:4d}: {line.rstrip()}")
