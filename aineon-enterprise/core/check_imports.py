#!/usr/bin/env python3
"""Check all imports in core system files"""

import ast
import os

files_to_check = [
    'unified_system.py',
    'tier_scanner.py',
    'tier_orchestrator.py',
    'tier_executor.py',
    'ai_optimizer.py',
    'profit_manager.py'
]

all_imports = set()
errors = []

for file in files_to_check:
    if not os.path.exists(file):
        errors.append(f"File not found: {file}")
        continue
    
    print(f"\n{file}:")
    with open(file, 'r') as f:
        try:
            tree = ast.parse(f.read())
            imports = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        mod = alias.name.split('.')[0]
                        imports.add(mod)
                        print(f"  import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        mod = node.module.split('.')[0]
                        imports.add(mod)
                        for alias in node.names:
                            print(f"  from {node.module} import {alias.name}")
            
            all_imports.update(imports)
        except SyntaxError as e:
            errors.append(f"{file}: {e}")

print("\n" + "=" * 70)
print("REQUIRED MODULES:")
for imp in sorted(all_imports):
    print(f"  {imp}")

if errors:
    print("\nERRORS:")
    for err in errors:
        print(f"  {err}")
