# Cabinet Ministers Dataset

## Overview

This dataset contains comprehensive information about all UK Cabinet Ministers from 1945 to present, extracted from the UK Parliament's data platform using the `pdpy` Python package.

## Generation

The dataset was generated using [cabinet_ministers.py](cabinet_ministers.py), which:

1. Fetches government roles for both MPs and Lords using `pdpy.fetch_mps_government_roles()` and `pdpy.fetch_lords_government_roles()`
2. Enriches the data with party membership information using `pdpy.fetch_mps_party_memberships()` and `pdpy.fetch_lords_party_memberships()`
3. Maps each government role to the appropriate Prime Minister based on the start date
4. Determines the Parliament session for each role using `pdpy.get_general_elections()`
5. Calculates tenure length (days in post) and Parliament duration (days parliament was in session)

## Dataset Statistics

- **Total Records**: 3,745 government role appointments
- **Date Range**: 1945-08-01 to 2025-09-16
- **Unique Ministers**: 1,156
- **Unique Posts**: 756
- **Unique Prime Ministers**: 18

### Distribution by Party

| Party            | Count |
| ---------------- | ----- |
| Conservative     | 2,294 |
| Labour           | 1,329 |
| Liberal Democrat | 77    |
| Other            | 4     |
| Crossbench       | 2     |

### Distribution by House

| House   | Count |
| ------- | ----- |
| Commons | 3,313 |
| Lords   | 432   |

### Prime Minister Coverage

Roles span from Winston Churchill (6 appointments) through Keir Starmer (113 appointments).

## Column Definitions

| Column                     | Description                                                           |
| -------------------------- | --------------------------------------------------------------------- |
| **given_name**             | First name of the minister                                            |
| **family_name**            | Last name of the minister                                             |
| **member_house**           | Which chamber they served in when holding the role (Commons or Lords) |
| **post**                   | The government position title                                         |
| **start_date**             | Date the minister took office (YYYY-MM-DD)                            |
| **end_date**               | Date the minister left office (YYYY-MM-DD)                            |
| **tenure_length_days**     | Number of days the minister held the post (end_date - start_date)     |
| **parliament_start_date**  | Date the Parliament session began (date of general election)          |
| **parliament_length_days** | Duration of the Parliament session in days                            |
| **party**                  | Political party affiliation during the government role                |
| **prime_minister**         | Name of the Prime Minister at the time the role started               |
| **person_id**              | Unique Parliament ID for the person                                   |
| **mnis_id**                | Member's Name Information Service ID (legacy Parliament system)       |

## Key Features

- **Historical Coverage**: Spans post-WWII UK government (1945-present)
- **Complete Data**: Includes both Commons and Lords members
- **Party Information**: Party affiliation is determined from the date the role started
- **PM Attribution**: Each role is linked to the Prime Minister in office at the time
- **Parliament Context**: Each role includes information about which Parliament was in session
- **Tenure Analysis**: Tenure length in days enables analysis of ministerial duration
- **Unique Identifiers**: Both modern Parliament IDs and legacy MNIS IDs are included

### Tenure Statistics

- **Average Tenure**: ~615 days (20 months)
- **Longest Tenure**: 5,388 days (~15 years)
- **Shortest Tenure**: 1 day
- **Average Parliament Duration**: ~1,586 days (~4.4 years)

## Notes on Data Quality

- Some party affiliations may be missing (NaN) for roles where party membership data is incomplete
- Government roles are inclusive of all ministers, not just Cabinet-level positions
- Posts range from senior ministerial positions to Parliamentary Whips and Under-Secretaries
- Multiple roles can be held simultaneously (not deduplicated)

## Usage Example

```python
import pandas as pd

# Load the dataset
df = pd.read_csv('cabinet_ministers.csv')

# Convert dates
df['start_date'] = pd.to_datetime(df['start_date'])
df['end_date'] = pd.to_datetime(df['end_date'])
df['parliament_start_date'] = pd.to_datetime(df['parliament_start_date'])

# Find all ministers under Tony Blair
blair_ministers = df[df['prime_minister'] == 'Tony Blair']
print(f"Tony Blair had {blair_ministers['mnis_id'].nunique()} unique ministers")

# Find longest-serving ministers
longest_serving = df.nlargest(10, 'tenure_length_days')[['given_name', 'family_name', 'post', 'tenure_length_days', 'prime_minister']]
print(longest_serving)

# Analyze tenure by parliament
df['parliament_year'] = df['parliament_start_date'].dt.year
avg_tenure_by_parliament = df.groupby('parliament_year')['tenure_length_days'].mean()
print(avg_tenure_by_parliament)

# Find a specific person's government roles
margaret_thatcher = df[df['family_name'] == 'Thatcher']
print(margaret_thatcher[['post', 'start_date', 'end_date', 'tenure_length_days', 'prime_minister']])
```

## Source

Data sourced from:

- **UK Parliament Data Platform**: https://beta.parliament.uk/
- **pdpy Package**: https://github.com/houseofcommonslibrary/pdpy

## Updates

To regenerate this dataset with the latest data:

```bash
python cabinet_ministers.py
```

A new timestamped extract directory will be created with the updated data.
