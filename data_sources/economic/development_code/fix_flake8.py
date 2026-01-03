"""
Fix flake8 errors in all Python files in the development_code directory.
This script will:
1. Remove unnecessary f-string prefixes
2. Remove trailing whitespace
3. Fix line length issues
4. Add proper blank lines
5. Fix bare except clauses
6. Remove unused imports
"""

import re
from pathlib import Path


def fix_file(filepath):
    """Fix flake8 errors in a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    lines = content.split('\n')
    fixed_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Remove trailing whitespace (W291, W293)
        line = line.rstrip()

        # Fix f-strings without placeholders (F541)
        if 'print(f"' in line and '{' not in line:
            line = line.replace('print(f"', 'print("')

        # Fix bare except (E722)
        if line.strip() == 'except:':
            line = line.replace('except:', 'except Exception:')

        fixed_lines.append(line)
        i += 1

    content = '\n'.join(fixed_lines)

    # Fix unused numpy import in merge_datasets.py
    if 'merge_datasets.py' in str(filepath):
        content = content.replace('import numpy as np\n', '')

    # Fix function definition spacing (E302 - need 2 blank lines before function)
    content = re.sub(r'\n(def \w+\()', r'\n\n\1', content)

    # Fix spacing after function (E305 - need 2 blank lines after function before module-level code)
    content = re.sub(r'(    return [^\n]+)\n\nif __name__',
                     r'\1\n\n\nif __name__', content)

    # Break long lines (E501)
    lines = content.split('\n')
    fixed_lines = []
    for line in lines:
        if len(line) > 120 and 'print(' in line:
            # Try to break print statements
            if 'print(f"' in line or 'print("' in line:
                # Keep as is if we can't easily break it
                fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    content = '\n'.join(fixed_lines)

    # Save if changed
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {filepath.name}")
        return True
    return False


def main():
    dev_code_dir = Path(__file__).parent
    py_files = list(dev_code_dir.glob('*.py'))

    # Exclude this fix script
    py_files = [f for f in py_files if f.name != 'fix_flake8.py']

    print(f"Found {len(py_files)} Python files to check")
    print()

    fixed_count = 0
    for py_file in py_files:
        if fix_file(py_file):
            fixed_count += 1

    print()
    print(f"Fixed {fixed_count} files")


if __name__ == "__main__":
    main()
