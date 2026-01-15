# Integration Checklist: dashboard_demo_readonly with UK Socio-Economic Modelling

**Purpose**: Track cross-repository integration and deduplication efforts
**Status**: Planning phase → Ready for implementation
**Last Updated**: January 15, 2026

---

## Phase 1: Parliament Periods Consolidation (PRIORITY 1)

### Preparation
- [ ] Read DEDUPLICATION_QUICK_START.md
- [ ] Review existing parliament periods output (23 records, 1945-2026)
- [ ] Verify dashboard_demo_readonly submodule is initialized
- [ ] Test pdpy API access

### Implementation: Create Shared Reference
- [ ] Create `data_sources/dashboard_demo_readonly/output/parliament_reference.csv`
  - [ ] Copy parliament data from existing extract OR
  - [ ] Generate fresh from `parliaments.py` main()
  - [ ] Verify 23 rows (parliaments 31-59)
  - [ ] Verify date range 1945-07-05 to 2026-01-15

### Implementation: Update cabinet_ministers.py
- [ ] Add `get_parliament_periods()` function with fallback logic
- [ ] Update imports to use new function
- [ ] Test cabinet ministers extraction with shared reference
- [ ] Verify output matches previous version

### Implementation: Update parliaments.py
- [ ] Add `save_parliament_reference()` function
- [ ] Call function in main() after generating periods
- [ ] Verify file saved to dashboard_demo_readonly/output

### Testing
- [ ] Run `test_parliament_deduplication.py` - ALL PASS
- [ ] Verify shared reference exists: parliament_reference.csv
- [ ] Verify cabinet_ministers.csv unchanged (comparison)
- [ ] Check file load time: <100ms expected
- [ ] Verify fallback works by temporarily moving shared reference

### Documentation
- [ ] Update DEVELOPER_REFERENCE.md with shared resource
- [ ] Document in parliament README.md
- [ ] Add example usage code
- [ ] Update INTEGRATION_GUIDE.md (create if not exists)

### Sign-Off
- [ ] Code review: parliament consolidation
- [ ] Test execution passed
- [ ] Documentation reviewed
- [ ] Merge to main branch

---

## Phase 2: Party Reference Extraction (PRIORITY 2)

### Discovery
- [ ] Identify all party classifications in UK Socio-Economic Modelling
  - [ ] cabinet_ministers.py (hardcoded government list)
  - [ ] mps.py (party extraction from pdpy)
  - [ ] party_membership.py (party membership handling)
- [ ] Document dashboard_demo party classifications
  - [ ] clean_and_enhance.py (Party_Group mapping)
  - [ ] Party switcher logic
  - [ ] Party grouping patterns

### Design
- [ ] Define party reference schema (name, group, historical_names, start_date, end_date)
- [ ] Determine scope: current parties only or historical?
- [ ] Decide: single source vs project-specific extensions

### Implementation: Create Shared Utility
- [ ] Create `dashboard_demo_readonly/utils/party_reference.py`
  - [ ] PARTY_MAPPING dictionary
  - [ ] PARTY_GROUPS dictionary (optional)
  - [ ] normalize_party_name() function
  - [ ] get_party_group() function
- [ ] Add docstrings and examples
- [ ] Add test cases

### Integration: Update parliament modules
- [ ] Update `cabinet_ministers.py` to import PARTY_MAPPING
- [ ] Update `party_membership.py` to use shared reference
- [ ] Verify party classification consistency
- [ ] Update any hardcoded party lists

### Integration: Dashboard Demo (readonly)
- [ ] Note what dashboard_demo could benefit from (reference only)
- [ ] No actual changes to dashboard_demo_readonly

### Testing
- [ ] Party classification tests pass
- [ ] Consistency checks: same party names across projects
- [ ] Historical party data (if included) validated
- [ ] Edge cases handled (None, unknown, etc.)

### Documentation
- [ ] Party reference schema documented
- [ ] Example usage in both projects
- [ ] Historical notes if applicable
- [ ] Update INTEGRATION_GUIDE.md

### Sign-Off
- [ ] Code review: party utility
- [ ] Integration testing passed
- [ ] Documentation reviewed
- [ ] Merge to main branch

---

## Phase 3: Data Quality Improvements (PRIORITY 3)

### Discovery
- [ ] Review dashboard_demo deduplication patterns
  - [ ] data_dedupe.py (name normalization functions)
  - [ ] Name standardization (diacritics, spacing, case)
  - [ ] Fuzzy matching algorithms
  - [ ] Registration number matching
- [ ] Identify candidate minister data for normalization

### Design
- [ ] Adapt dashboard_demo patterns for MP/minister names
- [ ] Define normalization scope (diacritics, suffixes, spacing)
- [ ] Plan testing strategy (sample minister data)

### Implementation
- [ ] Create or update name normalization function
  - [ ] Handle diacritics (é → e)
  - [ ] Handle suffixes (Jr., Sr., III)
  - [ ] Standardize spacing/capitalization
  - [ ] Handle special characters
- [ ] Add unit tests with real minister names
- [ ] Update matching logic in cabinet_ministers.py

### Integration
- [ ] Update `find_prime_minister()` to use normalized names
- [ ] Update minister matching logic
- [ ] Verify cabinet ministers matches improve
- [ ] Compare output before/after (diff)

### Testing
- [ ] Unit tests: name normalization
- [ ] Integration tests: cabinet ministers matching
- [ ] Edge cases: special characters, historical names
- [ ] Data quality metrics: before/after comparison

### Documentation
- [ ] Normalization rules documented
- [ ] Test cases documented
- [ ] Performance impact noted
- [ ] Update INTEGRATION_GUIDE.md

### Sign-Off
- [ ] Code review: data quality improvements
- [ ] Testing passed
- [ ] Data quality metrics verified
- [ ] Merge to main branch

---

## Phase 4: Logging Integration (PRIORITY 4)

### Discovery
- [ ] Review dashboard_demo logging setup
  - [ ] utils/logger.py implementation
  - [ ] @log_function_call decorator
  - [ ] Logger configuration
  - [ ] Log levels and usage patterns

### Design
- [ ] Decide: adopt dashboard_demo logger or create independent?
- [ ] Define logging levels for parliament module
- [ ] Plan logging strategy for data pipelines

### Implementation
- [ ] Import or create logging utility
- [ ] Add logging to parliament module functions
  - [ ] `get_parliament_periods()`
  - [ ] `get_cabinet_ministers_datafile()`
  - [ ] `fetch_mps_cabinet_roles()`
  - [ ] Other key functions
- [ ] Add @log_function_call decorators (optional)
- [ ] Configure log output (console, file, level)

### Testing
- [ ] Logging output verified
- [ ] Debug information captured correctly
- [ ] Performance impact minimal
- [ ] Log files readable and useful

### Documentation
- [ ] Logging configuration documented
- [ ] Log levels and usage explained
- [ ] Example log output shown
- [ ] Troubleshooting guide updated

### Sign-Off
- [ ] Code review: logging integration
- [ ] Testing passed
- [ ] Documentation reviewed
- [ ] Merge to main branch

---

## Ongoing: Documentation & Communication

### Create/Update Documentation Files
- [ ] **DEVELOPER_REFERENCE.md** - Add shared resources section
  - [ ] Parliament reference usage
  - [ ] Party reference usage
  - [ ] Shared utilities location
  - [ ] When to use dashboard_demo_readonly content
  
- [ ] **INTEGRATION_GUIDE.md** (new file)
  - [ ] Overview of shared resources
  - [ ] Architecture diagrams
  - [ ] Integration patterns
  - [ ] Troubleshooting
  - [ ] Contact/ownership info

- [ ] **README.md** (parliament module)
  - [ ] Note about shared references
  - [ ] Update data description
  - [ ] Link to integration guide

- [ ] **data_sources/dashboard_demo_readonly/README.md** 
  - [ ] Already created (Jan 15)
  - [ ] Verify still accurate
  - [ ] Link from DEVELOPER_REFERENCE

### Communication
- [ ] Announce shared resources to team
- [ ] Conduct knowledge-sharing session
- [ ] Add to onboarding documentation
- [ ] Update team wiki/knowledge base

### Monitoring & Maintenance
- [ ] Document maintenance schedule (if needed)
- [ ] Assign ownership of shared resources
- [ ] Create escalation procedures
- [ ] Plan periodic reviews

---

## Risk Mitigation

### Fallback Strategies
- [ ] Parliament reference: API fallback if CSV unavailable ✓
- [ ] Party reference: Graceful degradation if import fails ✓
- [ ] Logging: Optional enhancement, non-breaking ✓
- [ ] Data quality: Testing before/after with comparison ✓

### Rollback Plans
- [ ] Revert parliament reference: Use API calls only
- [ ] Revert party reference: Use original hardcoded lists
- [ ] Revert normalization: Use original matching logic
- [ ] Revert logging: Remove decorators, keep code

### Version Control
- [ ] Each phase in separate branch
- [ ] PR review before merge
- [ ] Tag version at each milestone
- [ ] Maintain changelog

---

## Success Metrics

### Parliament Periods (Phase 1)
- [ ] ✓ API call eliminated (load time <100ms)
- [ ] ✓ Shared reference exists and is correct
- [ ] ✓ Cabinet ministers output unchanged
- [ ] ✓ Both fallback and shared reference work

### Party Reference (Phase 2)
- [ ] ✓ Centralized party definitions
- [ ] ✓ Consistent classification across projects
- [ ] ✓ Maintainable in one location
- [ ] ✓ No hardcoded lists in source code

### Data Quality (Phase 3)
- [ ] ✓ Improved name matching accuracy
- [ ] ✓ Better handling of special cases
- [ ] ✓ Data quality metrics improved
- [ ] ✓ Tests document edge cases

### Logging (Phase 4)
- [ ] ✓ Structured logging implemented
- [ ] ✓ Audit trail captured
- [ ] ✓ Debugging visibility improved
- [ ] ✓ Performance impact <5%

### Overall
- [ ] ✓ Code reduction: 150-200 lines
- [ ] ✓ Dependencies documented
- [ ] ✓ Integration tested
- [ ] ✓ Team trained
- [ ] ✓ Maintenance plan in place

---

## Timeline Estimate

| Phase | Tasks | Effort | Duration |
|-------|-------|--------|----------|
| 1: Parliament | Implementation + Testing + Docs | 3-4 hrs | 1-2 days |
| 2: Party Ref | Discovery + Design + Implementation | 4-5 hrs | 2-3 days |
| 3: Data Quality | Discovery + Implementation + Testing | 5-6 hrs | 3-4 days |
| 4: Logging | Implementation + Integration + Docs | 2-3 hrs | 1-2 days |
| Documentation | Update guides, communicate | 3-4 hrs | 2-3 days |
| **TOTAL** | | **17-22 hrs** | **1-2 weeks** |

---

## Owner & Accountability

| Phase | Owner | Reviewer | Status |
|-------|-------|----------|--------|
| 1: Parliament | ✓ Assigned | TBD | 🟡 Ready |
| 2: Party Reference | TBD | TBD | 🔴 Awaiting |
| 3: Data Quality | TBD | TBD | 🔴 Awaiting |
| 4: Logging | TBD | TBD | 🔴 Awaiting |
| Documentation | TBD | TBD | 🔴 Awaiting |

---

## Related Documentation

- **DEDUPLICATION_ANALYSIS.md** - Comprehensive analysis (read first)
- **DEDUPLICATION_QUICK_START.md** - Parliament implementation guide
- **DEDUPLICATION_REVIEW_SUMMARY.md** - Executive summary
- **data_sources/dashboard_demo_readonly/README.md** - Setup instructions
- **DEVELOPER_REFERENCE.md** - Team documentation (update as you go)

---

## Sign-Off

### Phase Completion
Phase 1 Parliament Consolidation:
- [ ] Implementation complete
- [ ] Testing passed
- [ ] Documentation updated
- [ ] Merged to main
- **Sign-off date**: _____________

Phase 2 Party Reference:
- [ ] Implementation complete
- [ ] Testing passed
- [ ] Documentation updated
- [ ] Merged to main
- **Sign-off date**: _____________

Phase 3 Data Quality:
- [ ] Implementation complete
- [ ] Testing passed
- [ ] Documentation updated
- [ ] Merged to main
- **Sign-off date**: _____________

Phase 4 Logging:
- [ ] Implementation complete
- [ ] Testing passed
- [ ] Documentation updated
- [ ] Merged to main
- **Sign-off date**: _____________

---

**Last Updated**: January 15, 2026
**Status**: Ready for Phase 1 implementation
**Next Step**: Assign owner for Phase 1, begin parliament consolidation
