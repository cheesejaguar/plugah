import re
import sys
from pathlib import Path

def fix_unions(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern to match X | None
    pattern = r'(\w+(?:\[[\w\[\], ]+\])?)\s*\|\s*None'
    
    # Replace with Optional[X]
    def replace_union(match):
        type_str = match.group(1)
        return f'Optional[{type_str}]'
    
    new_content = re.sub(pattern, replace_union, content)
    
    # Check if Optional needs to be imported
    if 'Optional[' in new_content and 'from typing import' in new_content:
        # Find the typing import line
        import_pattern = r'from typing import ([^\\n]+)'
        match = re.search(import_pattern, new_content)
        if match:
            imports = match.group(1)
            if 'Optional' not in imports:
                # Add Optional to imports
                new_imports = imports.rstrip() + ', Optional'
                new_content = re.sub(import_pattern, f'from typing import {new_imports}', new_content, count=1)
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True
    return False

if __name__ == '__main__':
    files = sys.argv[1:]
    for filepath in files:
        if fix_unions(filepath):
            print(f"Fixed: {filepath}")
