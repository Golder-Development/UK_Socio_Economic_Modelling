# Documentation Automation Proposal

## Executive Summary

This document proposes a comprehensive automation system to keep project documentation synchronized with code and data reality. The goal is to eliminate manual documentation maintenance, reduce errors, and ensure documentation never drifts from actual implementation.

## ✅ Completed: Harmonized Category Automation

**Script:** `update_category_documentation.py`

**Status:** ✅ Implemented and validated (exit code 0, all 4 files updated)

**What it does:**
- Reads HARMONIZED_CATEGORIES dict directly from `build_harmonized_categories.py`
- Auto-generates formatted category lists (numbered, table format)
- Updates 4 documentation files:
  - HARMONIZED_QUICKSTART.md (category table)
  - HARMONIZED_CATEGORIES_README.md (numbered list)
  - METHODS_ICD_HARMONISATION.md (category count)
  - INDEX.md (category count)
- Uses marker-based updates to preserve manual content
- Validates category count consistency (26 categories)

**Time savings:** Eliminates 15-20 minutes of manual updates per category change

---

## 📋 Proposed Automations

### 1. Data Statistics Auto-Updater (HIGH PRIORITY)

**Script:** `update_data_statistics.py`

**Purpose:** Keep README statistics synchronized with actual data files

**What it would do:**
- Read actual data files (uk_mortality_by_cause_1901_onwards_harmonized.zip, etc.)
- Extract real statistics:
  - Row counts
  - Year ranges (min/max)
  - Category counts
  - File sizes
  - Column lists
- Update README.md and DATA_SUMMARY.md with actual values
- Prevent documentation claiming "2001-2025" when data is "1901-2017", etc.

**Markers needed:**
```markdown
<!-- DATA_STATS_START -->
Year range: 1901-2017
Total records: 1,465,808 rows
Categories: 27 (26 harmonized + 1 unmatched)
File size: 123.4 MB (compressed)
<!-- DATA_STATS_END -->
```

**Time savings:** 10-15 minutes per data regeneration

**Benefit:** Prevents embarrassing discrepancies between claimed and actual data coverage

---

### 2. File Inventory Auto-Generator (MEDIUM PRIORITY)

**Script:** `update_file_inventory.py`

**Purpose:** Auto-generate list of actual files in mortality_stats folder

**What it would do:**
- Scan mortality_stats/ folder for all CSV/ZIP files
- Generate formatted table:
  - Filename
  - Size
  - Last modified date
  - Row count (for CSVs)
  - Brief description (from filename pattern matching)
- Update DATA_SUMMARY.md and INDEX.md
- Flag files that exist but aren't documented
- Flag documentation references to missing files

**Example output:**
```markdown
<!-- FILE_INVENTORY_START -->
| File | Size | Last Modified | Rows | Description |
|------|------|---------------|------|-------------|
| uk_mortality_by_cause_1901_onwards_harmonized.zip | 43.2 MB | 2025-01-15 | 1,465,808 | Harmonized cause-of-death data |
| uk_mortality_yearly_totals_1901_2025.csv | 2.1 KB | 2025-01-15 | 125 | Annual death totals |
<!-- FILE_INVENTORY_END -->
```

**Time savings:** 20-30 minutes per major data update

**Benefit:** Ensures documentation references only files that actually exist

---

### 3. Dashboard Feature List Extractor (MEDIUM PRIORITY)

**Script:** `extract_dashboard_features.py`

**Purpose:** Document dashboard features by analyzing actual code

**What it would do:**
- Parse `create_interactive_mortality_dashboard.py`
- Extract control definitions (View mode, Category filter, Metric toggle)
- Extract trace types (Scatter, Bar, etc.)
- Generate feature documentation:
  - What controls exist
  - What options each control has
  - What trace types are used
  - What metrics are calculated
- Update dashboard documentation automatically

**Example output:**
```markdown
<!-- DASHBOARD_FEATURES_START -->
**Interactive Controls:**
1. **View Mode** (2 options): Unstacked Lines | Stacked Area
2. **Category Filter** (27 options): All, Infectious Diseases, Neoplasms, ...
3. **Metric Toggle** (3 options): per 100k | per 10k | Deaths

**Visualization:**
- Unstacked mode: Scatter traces with lines
- Stacked mode: Bar traces with barmode='stack'
<!-- DASHBOARD_FEATURES_END -->
```

**Time savings:** 15-20 minutes per dashboard enhancement

**Benefit:** Dashboard documentation never claims features that don't exist

---

### 4. Code Example Validator (LOW PRIORITY)

**Script:** `validate_code_examples.py`

**Purpose:** Ensure code snippets in documentation actually work

**What it would do:**
- Extract Python code blocks from all .md files
- Validate syntax
- Check imports are available
- Check file paths referenced in examples exist
- Check column names match actual data
- Report broken examples with line numbers

**Example report:**
```
⚠️ HARMONIZED_QUICKSTART.md:line 28
   Code references column 'old_column' but actual data has 'new_column'
   
⚠️ README.md:line 145
   Import 'import nonexistent_module' would fail
```

**Time savings:** 10-15 minutes per major code refactor

**Benefit:** Prevents users from copying non-functional code from documentation

---

### 5. Cross-Reference Validator (LOW PRIORITY)

**Script:** `validate_cross_references.py`

**Purpose:** Ensure all file/path references in documentation are valid

**What it would do:**
- Scan all .md files for file path references
- Check if referenced files actually exist
- Check for broken internal links between docs
- Validate relative paths
- Report broken references

**Example report:**
```
❌ README.md:line 67
   References 'data/old_file.csv' but file doesn't exist
   
❌ INDEX.md:line 34
   Links to 'MISSING_DOC.md' but file not found
```

**Time savings:** 5-10 minutes per major reorganization

**Benefit:** No more dead links in documentation

---

### 6. Dashboard List Auto-Updater (HIGH PRIORITY)

**Script:** `update_dashboard_list.py`

**Purpose:** Keep index.md dashboard list synchronized with generated_charts/

**What it would do:**
- Scan generated_charts/ for all .html files
- Generate formatted list with:
  - Dashboard name (extracted from title or filename)
  - Direct GitHub Pages URL
  - Age range (for age-based dashboards)
  - File size
  - Last updated
- Update index.md between markers
- Sort by logical order (main dashboards first, then age subsets)

**Example output:**
```markdown
<!-- GENERATED_CHARTS_START -->
### Mortality Dashboards

**Main Dashboards:**
- [Mortality Dashboard — Interactive](https://golder-development.github.io/UK_Socio_Economic_Modelling/generated_charts/mortality_dashboard_interactive.html) (4.69 MB, updated 2025-01-15)
- [Mortality Dashboard — Filtered](https://golder-development.github.io/UK_Socio_Economic_Modelling/generated_charts/mortality_dashboard_filtered.html) (4.73 MB, updated 2025-01-15)

**Age-Based Dashboards:**
- [Preschool (≤5)](https://golder-development.github.io/UK_Socio_Economic_Modelling/generated_charts/mortality_dashboard_age_preschool.html) (4.83 MB, updated 2025-01-15)
- [School Age (6–19)](https://golder-development.github.io/UK_Socio_Economic_Modelling/generated_charts/mortality_dashboard_age_school.html) (4.83 MB, updated 2025-01-15)
...
<!-- GENERATED_CHARTS_END -->
```

**Time savings:** 10-15 minutes per dashboard regeneration

**Benefit:** Dashboard list always matches what's actually published

---

### 7. Integration Script (HIGH PRIORITY)

**Script:** `regenerate_all_with_docs.py`

**Purpose:** Single command to regenerate everything and update all documentation

**What it would do:**
```python
# 1. Regenerate data
run('build_comprehensive_mortality_1901_2025.py')
run('build_harmonized_categories.py')

# 2. Regenerate dashboards
run('create_interactive_mortality_dashboard.py')

# 3. Update all documentation
run('update_category_documentation.py')
run('update_data_statistics.py')
run('update_file_inventory.py')
run('update_dashboard_list.py')
run('extract_dashboard_features.py')

# 4. Validate
run('validate_code_examples.py')
run('validate_cross_references.py')

# 5. Report
print_summary_of_changes()
```

**Time savings:** Eliminates 60-90 minutes of manual work per major update

**Benefit:** One command ensures everything stays synchronized

---

## Implementation Priority

### Phase 1 (Immediate - 2 hours)
1. ✅ Harmonized category automation (DONE)
2. Data statistics auto-updater
3. Dashboard list auto-updater
4. Integration script (basic version)

### Phase 2 (Next session - 3 hours)
5. File inventory auto-generator
6. Dashboard feature list extractor
7. Integration script (full version with validation)

### Phase 3 (Future enhancement - 2 hours)
8. Code example validator
9. Cross-reference validator
10. CI/CD integration (run on git pre-commit)

---

## Estimated Time Savings

**Per major update cycle:**
- Manual documentation updates: 90-120 minutes
- With automation: 5-10 minutes (just run one script)
- **Time saved: 80-110 minutes per cycle**

**Over project lifetime (assuming 20 major updates):**
- Manual approach: 30-40 hours
- Automated approach: 2-3 hours
- **Total time saved: 27-37 hours**

**Break-even point:** After implementing automation (7 hours), savings achieved after just 4-5 major updates.

---

## Risk Mitigation

**Risk 1: Scripts break when code changes**
- Mitigation: Use marker-based updates that fail gracefully
- Scripts should report what they can't update, not crash

**Risk 2: Scripts overwrite manual documentation**
- Mitigation: Only update content between markers
- Manual sections remain untouched
- Git diff shows exactly what changed

**Risk 3: False sense of accuracy**
- Mitigation: Validators report confidence levels
- "Auto-generated" tags on all automated sections
- Regular manual audits recommended

---

## Next Steps

1. ✅ Implement category automation (COMPLETED)
2. ✅ Update all old filename references (COMPLETED)
3. 🔄 Implement data statistics updater (IN PROGRESS)
4. Implement dashboard list updater
5. Create integration script
6. Test full automation pipeline
7. Document automation system itself
8. Set up git pre-commit hooks (optional)

---

## Conclusion

This automation system will:
- ✅ Eliminate 80-110 minutes of manual work per update
- ✅ Prevent documentation drift from reality
- ✅ Catch broken references and examples automatically
- ✅ Make documentation maintenance nearly effortless
- ✅ Allow focus on analysis rather than documentation upkeep

**Recommendation:** Proceed with Phase 1 implementation immediately (data statistics + dashboard list + integration script).
