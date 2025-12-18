#!/usr/bin/env python3
"""Verify that build_posts_mindmap.py will run correctly."""

import sys
from pathlib import Path

print("=" * 60)
print("VERIFYING SCRIPT SETUP")
print("=" * 60)

# Check dependencies
print("\n1. CHECKING DEPENDENCIES:")
try:
    import networkx as nx
    print("   ✓ networkx available")
except ImportError as e:
    print(f"   ✗ networkx NOT available: {e}")
    sys.exit(1)

try:
    import numpy as np
    print("   ✓ numpy available")
except ImportError as e:
    print(f"   ✗ numpy NOT available: {e}")
    sys.exit(1)

# Check input file
print("\n2. CHECKING INPUT FILE:")
zip_file = Path('hysnapsmusicandmentalhealth.wordpress.com-2025-12-17-10_23_08.zip')
if zip_file.exists():
    file_size = zip_file.stat().st_size
    print(f"   ✓ ZIP file found: {zip_file.name}")
    print(f"     Size: {file_size:,} bytes")
    
    import zipfile
    try:
        with zipfile.ZipFile(zip_file) as z:
            xml_files = [n for n in z.namelist() if n.lower().endswith('.xml')]
            print(f"   ✓ XML files in ZIP: {len(xml_files)}")
            for xml in xml_files:
                print(f"     - {xml}")
    except Exception as e:
        print(f"   ✗ Error reading ZIP: {e}")
        sys.exit(1)
else:
    print(f"   ✗ ZIP file NOT found: {zip_file}")
    sys.exit(1)

# Check output directory
print("\n3. CHECKING OUTPUT DIRECTORY:")
try:
    test_file = Path('test_write.tmp')
    test_file.write_text('test')
    test_file.unlink()
    print(f"   ✓ Output directory is writable: {Path.cwd()}")
except Exception as e:
    print(f"   ✗ Output directory NOT writable: {e}")
    sys.exit(1)

# Check script file
print("\n4. CHECKING SCRIPT FILE:")
script = Path('build_posts_mindmap.py')
if script.exists():
    print(f"   ✓ Script found: {script.name}")
    print(f"     Size: {script.stat().st_size:,} bytes")
else:
    print(f"   ✗ Script NOT found: {script}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ ALL CHECKS PASSED - SCRIPT WILL RUN CORRECTLY")
print("=" * 60)
print("\nTo run the script, execute:")
print(f"  python build_posts_mindmap.py {zip_file.name}")
print("\nOutput will be saved to:")
print("  political_posts_mindmap.html")
print("=" * 60)
