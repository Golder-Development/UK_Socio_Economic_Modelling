# Related Repositories

## Dashboard Demo Repository

**Repository**: https://github.com/Golder-Development/dashboard_demo

**Relationship**: Separate but complementary project with significant work on UK Parliament data structures, members of parliament, and parliamentary analysis.

### What's in Dashboard Demo

The dashboard_demo repository contains:

- Parliamentary member data structures and utilities
- MP/Lords member enrichment and processing
- Parliament session analysis and manipulation
- Visualization dashboards for parliamentary data
- Member activity tracking and aggregation
- Party and constituency data management

### How It Relates to This Project

This project (`UK_Socio_Economic_Modelling/data_sources/parliament/`) focuses on:

- **Cabinet ministers analysis** - Government positions and turnover
- **Secretary of State churn** - Ministerial appointment patterns
- **Tenure analysis** - Duration of service in roles
- **Parliament-based aggregation** - Churn metrics by parliament

The dashboard_demo repo provides:

- **Lower-level data** - Member and parliament foundations
- **Broader scope** - All MPs and Lords, not just government
- **Infrastructure** - Data structures and processing utilities

### Integration Points

Both projects can use:

- **Parliament periods data** - Start/end dates of parliaments
- **Member IDs** - Person identifiers (mnis_id, parliament_id)
- **Party affiliations** - Political party membership
- **Historical records** - Member service timelines

### When to Use Each

**Use UK_Socio_Economic_Modelling** for:

- Cabinet minister analysis
- Government turnover metrics
- Minister tenure patterns
- Secretary of State statistics

**Use dashboard_demo** for:

- General member data
- Broader parliamentary analysis
- Dashboard visualizations
- Member activity patterns

### Maintaining Separately

These repositories should be maintained independently because:

1. Different scopes (government only vs. all members)
2. Different data extraction sources (can vary by project)
3. Different analysis goals (ministerial vs. broader)
4. Potential for divergent development paths

### Referencing Between Projects

If you need to reference structures or utilities from dashboard_demo:

1. **Don't create hard dependencies** - Keep projects independent
2. **Copy relevant code** if needed for this project's independence
3. **Document the sources** - Note where code originated
4. **Update both if fundamentally improving** - Share improvements that benefit both

### Data Consistency

Both projects may use:

- Parliament periods (currently cached locally here)
- Member IDs from Parliament API
- Party membership data
- Historical dates

**Important**: Each project maintains its own caches and extracts to ensure independence.

---

## Example Data Structures

### Parliament Periods

Both projects may need parliament session dates. This project caches locally in:

```
data_sources/parliament/most recent output/parliaments_periods.json
```

Dashboard_demo may have similar structure - check its parliament data handling.

### Member Records

Cabinet ministers here reference members via:

- `person_id` - Internal identifier from parliament API
- `mnis_id` - UK Parliament MNIS identifier
- `given_name`, `family_name` - Person names
- `member_house` - Commons/Lords

Dashboard_demo likely has more comprehensive member records.

---

## Accessing Dashboard Demo Resources

### Repository Structure

```
dashboard_demo/
├── data/           # Data extracts and outputs
├── src/            # Python utilities and processing
├── dashboards/     # Visualization code
└── parliament/     # Parliament-specific code
```

### Key Files to Reference

- Parliament session dates
- Member ID mappings
- Data processing utilities
- Visualization patterns

### Contact/Collaboration

If improving parliament data handling:

1. Work in your respective repository
2. Document improvements
3. Reference the other repo if sharing patterns
4. Coordinate if fixing shared data sources

---

## Maintenance Notes

### This Project (UK_Socio_Economic_Modelling)

- **Focus**: Cabinet ministers and government turnover
- **Data Source**: Parliament API via `pdpy`
- **Update Frequency**: As needed for analysis
- **Python Version**: 3.10+

### Dashboard Demo Project

- **Focus**: Broader parliamentary analysis
- **Data Sources**: May vary (check its documentation)
- **Update Frequency**: Check project status
- **Python Version**: Check project requirements

### Syncing Parliament Data

If parliament periods data needs updating:

1. Update in one project's cache
2. Document the parliament changes
3. Reference in other project if needed
4. Share the parliament periods JSON if helpful

---

## Example: Using Parliament Data from Dashboard Demo

If dashboard_demo has useful parliament processing:

```python
# Don't do this (creates hard dependency):
from dashboard_demo.parliament import get_parliaments

# Instead do this (maintain independence):
# Copy the useful function into your project:
def get_parliaments():
    """
    Copied from dashboard_demo.parliament module
    Original: https://github.com/Golder-Development/dashboard_demo/src/parliament.py
    """
    # Implementation here...
```

This keeps both projects independent while allowing knowledge sharing.

---

**Last Updated**: January 15, 2026
**Status**: Active (separate repositories)
**Coordination**: Document improvements; sync when beneficial
