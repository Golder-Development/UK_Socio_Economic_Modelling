# Mortality Rate Denominator Examples

This document shows **correct** vs **incorrect** use of the new age-group mortality rates.

---

## ❌ INCORRECT: Mixing Denominators

### Mistake 1: Unmarked rates (ambiguous denominator)

```python
# ❌ BAD: Reader doesn't know which denominator
print("Elderly mortality was 18,824 in 2000")
print("Child mortality was 139.3 in 2000")
print("Therefore elderly are 135× deadlier than children")
```

**Problem:** 18,824 is per 100k of **85+ population** (277,000 people)  
13 9.3 is per 100k of **0-4 population** (1,613,300 people)

If comparing to overall population (52M), these rates are incomparable!

### Mistake 2: Comparing across different denominators

```python
# ❌ BAD: Mixing age-group and population-wide rates
by_age = pd.read_csv('by_age_group.csv')  # denominators: each age group
yearly = pd.read_csv('yearly_totals.csv')  # denominator: total population

# This is WRONG - different denominators!
age_2000 = by_age[(by_age['year'] == 2000) & (by_age['age_group'] == '85+')]
year_2000 = yearly[yearly['year'] == 2000]

# ❌ Don't do this:
ratio = age_2000['mortality_rate_per_100k_age_group_population'].values[0] / \
        year_2000['mortality_rate_per_100k_total_population'].values[0]
print(f"85+ is {ratio}× higher than overall")  # MEANINGLESS RATIO
```

**Problem:** Dividing 18,824 (per 85+ population) by 1,032 (per total population) gives a meaningless number (17.2×).

### Mistake 3: Unmarked charts

```python
# ❌ BAD: Chart without denominator label
fig.update_layout(yaxis_title="Mortality Rate (per 100k)")  # Too vague!
```

**Problem:** Viewer doesn't know if:
- Each age group uses its own population
- All are per total population
- Mix of denominators

---

## ✅ CORRECT: Explicit Denominators

### Correct 1: Always label the denominator

```python
# ✅ GOOD: Clear what denominator is used
print("Elderly (85+) mortality: 18,824 per 100,000 [of 85+ population in 2000]")
print("Children (0-4) mortality: 139.3 per 100,000 [of 0-4 population in 2000]")
print("Ratio: 135.2× (comparing within their respective age groups)")
```

**Why it works:** Reader immediately understands the denominator for each rate.

### Correct 2: Use appropriate file for your question

**Question:** "How does elderly mortality compare to children?"  
✅ **Use:** `by_age_group.csv` (both use age-group denominators)

```python
by_age = pd.read_csv('uk_mortality_rates_per_100k_by_age_group.csv')

year_2000 = by_age[by_age['year'] == 2000]
elderly = year_2000[(year_2000['age_group'] == '85+') & (year_2000['sex'] == 'Male')]
children = year_2000[(year_2000['age_group'] == '0-4') & (year_2000['sex'] == 'Male')]

elderly_rate = elderly['mortality_rate_per_100k_age_group_population'].values[0]  # 18824.2
children_rate = children['mortality_rate_per_100k_age_group_population'].values[0]  # 139.3

ratio = elderly_rate / children_rate  # 135.2× - VALID COMPARISON
print(f"✓ 85+ males are {ratio:.1f}× more likely to die than 0-4 males")
print(f"  (Both rates per 100k of their respective age group populations)")
```

### Correct 3: Include denominator in visualization

```python
import plotly.graph_objects as go

# ✅ GOOD: Explicit denominator in titles and labels
fig = go.Figure()

for age_group in ['0-4', '25-34', '65-74', '85+']:
    data = by_age[(by_age['age_group'] == age_group) & (by_age['sex'] == 'Male')]
    fig.add_trace(go.Scatter(
        x=data['year'],
        y=data['mortality_rate_per_100k_age_group_population'],
        name=age_group
    ))

fig.update_layout(
    title="Male Mortality by Age Group (1901–2000)",
    yaxis_title="Deaths per 100,000<br>[of each age group's population]",  # ← EXPLICIT
    hovertemplate="<b>%{name}</b><br>Year: %{x}<br>Rate: %{y:.0f} per 100k<extra></extra>"
)
fig.show()
```

### Correct 4: Document denominator in code comments

```python
# ✅ GOOD: Document which file and denominator you're using
def analyze_disease_by_age():
    """
    Analyze disease burden across age groups.
    
    Data source: uk_mortality_rates_per_100k_by_cause.csv
    Denominator: Each age group's population (not total population)
    
    This allows fair comparison of causes within each age group.
    """
    by_cause = pd.read_csv('uk_mortality_rates_per_100k_by_cause.csv')
    
    # Filter to infectious disease in 2000
    infections_2000 = by_cause[
        (by_cause['year'] == 2000) & 
        (by_cause['cause'] == 'Infectious Disease')
    ]
    
    # Compare across age groups
    # These are all per 100k OF EACH AGE GROUP
    print("Infectious disease rates (per 100,000 of each age group):")
    for _, row in infections_2000.iterrows():
        print(f"  {row['age_group']:>6}: {row['mortality_rate_per_100k_age_group_population']:>8.1f}")
```

### Correct 5: Population-wide statements use yearly_totals

```python
# ✅ GOOD: Use yearly_totals for overall population statements
yearly = pd.read_csv('uk_mortality_rates_per_100k_yearly_totals.csv')

rate_1901 = yearly[yearly['year'] == 1901]['mortality_rate_per_100k_total_population'].values[0]
rate_2000 = yearly[yearly['year'] == 2000]['mortality_rate_per_100k_total_population'].values[0]
improvement = (1 - rate_2000 / rate_1901) * 100

print(f"✓ UK population mortality improved {improvement:.1f}% from 1901 to 2000")
print(f"  1901: {rate_1901:.0f} per 100,000 (total population)")
print(f"  2000: {rate_2000:.0f} per 100,000 (total population)")
```

---

## 🎯 Decision Tree: Which File to Use?

```
Question about mortality?
│
├─→ "How do causes differ WITHIN an age group?"
│   └─→ Use: by_cause.csv
│       Denominator: age-group population
│       Column: mortality_rate_per_100k_age_group_population
│       Example: "Is TB deadlier than pneumonia in 65-74 year-olds?"
│
├─→ "How do age groups compare to EACH OTHER?"
│   └─→ Use: by_age_group.csv
│       Denominator: each age group's population
│       Column: mortality_rate_per_100k_age_group_population
│       Example: "Do elderly die at higher rates than middle-aged?"
│
└─→ "What's the OVERALL population trend over time?"
    └─→ Use: yearly_totals.csv
        Denominator: total population
        Column: mortality_rate_per_100k_total_population
        Example: "Has overall UK mortality improved since 1901?"
```

---

## 📋 Checklist: Before Publishing a Result

- [ ] I identified which file I used (by_cause / by_age_group / yearly_totals)
- [ ] I included the denominator in my statement or caption
- [ ] I didn't mix rates with different denominators
- [ ] My column name is explicitly labeled (`_age_group_population` or `_total_population`)
- [ ] Charts/visualizations clearly state the denominator on the y-axis
- [ ] Code comments document which denominator applies

---

## 🔗 Cross-File Safety

**If combining data from different files, rename columns:**

```python
# ⚠️ BAD: This will be confusing
by_age = pd.read_csv('by_age_group.csv')  # _age_group_population
yearly = pd.read_csv('yearly_totals.csv')  # _total_population
combined = pd.concat([by_age, yearly])  # Mixed denominators!

# ✅ GOOD: Explicitly rename to avoid confusion
by_age = pd.read_csv('by_age_group.csv')
by_age = by_age.rename(columns={
    'mortality_rate_per_100k_age_group_population': 'rate_per_100k_age_group'
})

yearly = pd.read_csv('yearly_totals.csv')
yearly = yearly.rename(columns={
    'mortality_rate_per_100k_total_population': 'rate_per_100k_total'
})

# Now the column names clearly distinguish the denominators
```

---

## 💡 Summary

✅ **DO:**
- Always include the denominator in results/charts
- Use the file appropriate for your question
- Rename columns when combining data from different sources
- Document denominator in code/comments

❌ **DON'T:**
- Report rates without specifying denominator
- Compare rates with different denominators
- Use `mortality_rate_per_100k` without context (use explicit column names)
- Mix by_age with yearly_totals unless carefully labeled

