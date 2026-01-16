# GitHub Pages Compatibility Fixes

## Summary of Changes

This update ensures all generated charts are fully compatible with GitHub Pages hosting.

## Changes Made

### 1. **Code Fixes**

#### `visuals/political_donations_interactive.py`

- **Improved filename sanitization** for party-specific charts
- Removes dots, parentheses, consecutive underscores/dashes
- Example: `"Democratic Unionist Party - D.U.P."` → `donations_by_party_democratic_unionist_party_dup.html`

#### `visuals/pension_reform_impact_analysis.py`

- **Added proper Path() usage** for cross-platform compatibility
- Uses relative paths from script location
- Ensures CSV files also use proper paths

#### `visuals/final_year_pension_analysis.py`

- **Added proper Path() usage** for cross-platform compatibility
- Consistent with other scripts

### 2. **New Files Created**

#### `.nojekyll` (root directory)

- Tells GitHub Pages to **not use Jekyll processing**
- Prevents issues with files/folders starting with `_`
- Essential for proper rendering

#### `generated_charts/index.html`

- **Beautiful navigation page** for all generated charts
- Organized by category:
  - Political Donations (8 charts)
  - Cabinet & Parliamentary Analysis (5 charts)
  - Mortality & Demographics (3 charts)
  - Network Visualizations (2 charts)
- Responsive design with hover effects
- Direct links to GitHub repository and blog

#### `visuals/check_github_pages_compatibility.py`

- **Validation script** to check all HTML files
- Checks performed:
  1. File size limits (< 90MB)
  2. Plotly CDN usage (not embedded)
  3. Filename validity (no problematic characters)
  4. Absolute paths (none should exist)
  5. Required files (.nojekyll, index.html)

## Key GitHub Pages Compatibility Issues Fixed

### ✅ File Size

- All `write_html()` calls use `include_plotlyjs='cdn'`
- Prevents 3MB+ embedded library
- Keeps files under GitHub's 100MB limit

### ✅ Filenames

- No dots (except .html extension)
- No spaces or parentheses
- No consecutive underscores/dashes
- All lowercase for consistency

### ✅ Paths

- All scripts use `Path()` for cross-platform compatibility
- Relative paths only (no `C:\` or `file://`)
- Consistent structure across codebase

### ✅ Jekyll Compatibility

- `.nojekyll` file prevents Jekyll processing
- No underscore-prefixed files to worry about

### ✅ Navigation

- `index.html` provides entry point
- Users can browse all charts easily
- Professional appearance

## Usage

### Run Compatibility Checker

```powershell
cd h:\VScode\UK_Socio_Economic_Modelling
python visuals/check_github_pages_compatibility.py
```

### Regenerate Charts (to apply filename fixes)

```powershell
python visuals/political_donations_interactive.py
```

### View Locally

Open `generated_charts/index.html` in your browser to preview.

### Deploy to GitHub Pages

1. Commit all changes
2. Push to GitHub
3. Enable GitHub Pages in repository settings:
   - Settings → Pages
   - Source: Deploy from branch
   - Branch: main
   - Folder: / (root)
4. Access at: `https://golder-development.github.io/UK_Socio_Economic_Modelling/generated_charts/`

## Verification Checklist

After running the compatibility checker, verify:

- [ ] All HTML files < 90MB
- [ ] All files use Plotly CDN (no embedded library)
- [ ] No problematic characters in filenames
- [ ] No absolute paths in HTML
- [ ] `.nojekyll` exists in root
- [ ] `generated_charts/index.html` exists
- [ ] Charts load correctly in browser
- [ ] Links work on GitHub Pages

## Before vs After

### Before

❌ `donations_by_party_democratic_unionist_party_-_d.u.p..html`
❌ Embedded 3MB Plotly library in some files
❌ Hardcoded paths: `'generated_charts/file.html'`
❌ No index page - users had to know filenames

### After

✅ `donations_by_party_democratic_unionist_party_dup.html`
✅ All files use CDN: `include_plotlyjs='cdn'`
✅ Path() usage: `Path(__file__).parent.parent / "generated_charts"`
✅ Beautiful index.html with navigation

## Testing

The compatibility checker will report any issues:

```
================================================================================
GitHub Pages Compatibility Checker
================================================================================

Found 25 HTML files

================================================================================
1. FILE SIZE CHECK
================================================================================

[OK] All files within size limits (< 90MB)

================================================================================
2. PLOTLY CDN CHECK
================================================================================

[OK] All files use Plotly CDN correctly

================================================================================
3. FILENAME VALIDATION
================================================================================

[OK] All filenames are GitHub Pages compatible

================================================================================
4. ABSOLUTE PATH CHECK
================================================================================

[OK] No absolute paths detected

================================================================================
REQUIRED FILES CHECK
================================================================================
  ✅ index.html exists
  ✅ .nojekyll exists

✅ All checks passed! Files are GitHub Pages compatible.
```

## Notes

- **All existing functionality preserved** - only compatibility improvements
- **No breaking changes** to chart generation logic
- **Backwards compatible** - old filenames still work locally
- **Future-proof** - Path() works on Windows, Mac, Linux

## Links

- **Live Site**: https://golder-development.github.io/UK_Socio_Economic_Modelling/generated_charts/
- **Repository**: https://github.com/Golder-Development/UK_Socio_Economic_Modelling
- **Blog**: https://hysnapsmusicandmentalhealth.wordpress.com/
