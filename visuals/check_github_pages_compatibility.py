"""
GitHub Pages Compatibility Checker
====================================

This script validates that generated HTML files are compatible with GitHub Pages:
1. Checks file sizes (GitHub has limits)
2. Verifies Plotly is loaded from CDN (not embedded)
3. Validates filenames (no problematic characters)
4. Checks for relative paths
5. Lists all HTML files in generated_charts
"""

from pathlib import Path
import re

# Configuration
GENERATED_CHARTS_DIR = Path(__file__).parent.parent / "generated_charts"
MAX_FILE_SIZE_MB = 90  # GitHub Pages has 100MB limit, keep buffer
PROBLEMATIC_CHARS = ['.', '-', ' ', '(', ')']

def check_file_size(file_path: Path) -> dict:
    """Check if file size is within GitHub Pages limits."""
    size_mb = file_path.stat().st_size / (1024 * 1024)
    return {
        'path': file_path.name,
        'size_mb': round(size_mb, 2),
        'ok': size_mb < MAX_FILE_SIZE_MB,
        'issue': f"File too large: {size_mb:.2f}MB" if size_mb >= MAX_FILE_SIZE_MB else None
    }

def check_plotly_cdn(file_path: Path) -> dict:
    """Check if Plotly is loaded from CDN instead of embedded."""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        # Check for embedded Plotly (large inline script)
        has_embedded_plotly = 'plotly.js v' in content and len(content) > 500000
        
        # Check for CDN reference
        has_cdn = 'cdn.plot.ly' in content or 'plotly-latest.min.js' in content
        
        issue = None
        if has_embedded_plotly:
            issue = "Plotly library is embedded (file too large)"
        elif not has_cdn and 'Plotly' in content:
            issue = "Plotly reference found but CDN not detected"
        
        return {
            'path': file_path.name,
            'has_cdn': has_cdn,
            'embedded': has_embedded_plotly,
            'ok': has_cdn and not has_embedded_plotly,
            'issue': issue
        }
    except Exception as e:
        return {
            'path': file_path.name,
            'has_cdn': False,
            'embedded': False,
            'ok': False,
            'issue': f"Error reading file: {e}"
        }

def check_filename(file_path: Path) -> dict:
    """Check for problematic characters in filename."""
    name = file_path.name
    
    # Check for multiple dots (except .html)
    dots_count = name.count('.') - 1  # Subtract the .html extension
    
    # Check for problematic patterns
    issues = []
    if dots_count > 0:
        issues.append(f"Contains {dots_count} extra dot(s)")
    if '--' in name or '__' in name:
        issues.append("Contains consecutive dashes/underscores")
    if '(' in name or ')' in name:
        issues.append("Contains parentheses")
    if ' ' in name:
        issues.append("Contains spaces")
    
    return {
        'path': name,
        'ok': len(issues) == 0,
        'issue': '; '.join(issues) if issues else None
    }

def check_absolute_paths(file_path: Path) -> dict:
    """Check for absolute paths that won't work on GitHub Pages."""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        # Look for common absolute path patterns
        issues = []
        if re.search(r'file:///', content):
            issues.append("Contains file:// protocol")
        if re.search(r'[A-Z]:\\', content):
            issues.append("Contains Windows absolute path")
        if re.search(r'src=["\'][A-Z]:', content):
            issues.append("Contains absolute path in src attribute")
        
        return {
            'path': file_path.name,
            'ok': len(issues) == 0,
            'issue': '; '.join(issues) if issues else None
        }
    except Exception as e:
        return {
            'path': file_path.name,
            'ok': True,  # Assume OK if can't read
            'issue': None
        }

def main():
    """Run all compatibility checks."""
    print("=" * 80)
    print("GitHub Pages Compatibility Checker")
    print("=" * 80)
    
    if not GENERATED_CHARTS_DIR.exists():
        print(f"\n[ERROR] Directory not found: {GENERATED_CHARTS_DIR}")
        return
    
    # Get all HTML files
    html_files = list(GENERATED_CHARTS_DIR.glob("*.html"))
    
    if not html_files:
        print(f"\n[ERROR] No HTML files found in {GENERATED_CHARTS_DIR}")
        return
    
    print(f"\nFound {len(html_files)} HTML files\n")
    
    # Run checks
    all_ok = True
    
    # 1. File size check
    print("\n" + "=" * 80)
    print("1. FILE SIZE CHECK")
    print("=" * 80)
    size_issues = []
    for html_file in sorted(html_files):
        result = check_file_size(html_file)
        if not result['ok']:
            size_issues.append(result)
            all_ok = False
    
    if size_issues:
        print(f"\n[WARNING] {len(size_issues)} file(s) exceed size limits:")
        for issue in size_issues:
            print(f"  ❌ {issue['path']}: {issue['size_mb']}MB ({issue['issue']})")
    else:
        print(f"\n[OK] All files within size limits (< {MAX_FILE_SIZE_MB}MB)")
    
    # 2. Plotly CDN check
    print("\n" + "=" * 80)
    print("2. PLOTLY CDN CHECK")
    print("=" * 80)
    cdn_issues = []
    for html_file in sorted(html_files):
        result = check_plotly_cdn(html_file)
        if not result['ok']:
            cdn_issues.append(result)
            all_ok = False
    
    if cdn_issues:
        print(f"\n[WARNING] {len(cdn_issues)} file(s) have Plotly issues:")
        for issue in cdn_issues:
            print(f"  ❌ {issue['path']}: {issue['issue']}")
    else:
        print("\n[OK] All files use Plotly CDN correctly")
    
    # 3. Filename check
    print("\n" + "=" * 80)
    print("3. FILENAME VALIDATION")
    print("=" * 80)
    filename_issues = []
    for html_file in sorted(html_files):
        result = check_filename(html_file)
        if not result['ok']:
            filename_issues.append(result)
            all_ok = False
    
    if filename_issues:
        print(f"\n[WARNING] {len(filename_issues)} file(s) have problematic filenames:")
        for issue in filename_issues:
            print(f"  ⚠️  {issue['path']}: {issue['issue']}")
    else:
        print("\n[OK] All filenames are GitHub Pages compatible")
    
    # 4. Absolute path check
    print("\n" + "=" * 80)
    print("4. ABSOLUTE PATH CHECK")
    print("=" * 80)
    path_issues = []
    for html_file in sorted(html_files):
        result = check_absolute_paths(html_file)
        if not result['ok']:
            path_issues.append(result)
            all_ok = False
    
    if path_issues:
        print(f"\n[WARNING] {len(path_issues)} file(s) contain absolute paths:")
        for issue in path_issues:
            print(f"  ❌ {issue['path']}: {issue['issue']}")
    else:
        print("\n[OK] No absolute paths detected")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if all_ok:
        print("\n✅ All checks passed! Files are GitHub Pages compatible.")
    else:
        print("\n⚠️  Some issues found. Review warnings above.")
        print("\nRecommended actions:")
        if size_issues:
            print("  • Regenerate large files with include_plotlyjs='cdn'")
        if cdn_issues:
            print("  • Ensure all charts use include_plotlyjs='cdn'")
        if filename_issues:
            print("  • Rename files to remove special characters")
        if path_issues:
            print("  • Use relative paths only")
    
    # Check for required files
    print("\n" + "=" * 80)
    print("REQUIRED FILES CHECK")
    print("=" * 80)
    
    required_files = {
        'index.html': GENERATED_CHARTS_DIR / 'index.html',
        '.nojekyll': GENERATED_CHARTS_DIR.parent / '.nojekyll'
    }
    
    for name, path in required_files.items():
        if path.exists():
            print(f"  ✅ {name} exists")
        else:
            print(f"  ❌ {name} missing (create it for GitHub Pages)")
            all_ok = False
    
    print("\n" + "=" * 80)
    print(f"\nTotal HTML files: {len(html_files)}")
    print(f"Issues found: {len(size_issues) + len(cdn_issues) + len(filename_issues) + len(path_issues)}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
