# Lexicon Conflict Analysis Report
**Generated:** January 2, 2026  
**Workspace:** UK_Socio_Economic_Modelling  
**Analysis Path:** data_sources/mortality_stats/socio_economic_classification/lexicons/

---

## Executive Summary

The lexicon system contains **10 classification categories** with **301 total terms** (all unique - no exact duplicates across lexicons). The analysis reveals a well-designed lexicon structure with **minimal critical conflicts**, but several **semantic ambiguities** that could affect classification accuracy.

### Key Statistics
- **Total terms:** 301
- **Unique terms:** 301 (100%)
- **Cross-lexicon exact duplicates:** 0
- **Within-lexicon conflicts:** 0
- **Substring overlaps:** 2
- **Semantic ambiguities:** 7 root patterns across multiple lexicons

---

## 1. CRITICAL FINDINGS ⚠️

### 1.1 Substring Overlaps (Within Same Lexicon)
**Impact:** Double-counting risk

#### Issue 1: Neonatal Terms (L1_02_Maternal_and_Early-Life_Mortality)
- **Substring:** `neonat` (weight: 9.0)
- **Token:** `neonatal` (weight: 9.0)
- **Problem:** Both will match the word "neonatal", potentially adding 18 weight instead of 9
- **Recommendation:** Remove the substring entry; the token match is sufficient

#### Issue 2: Deformity Terms (L1_03_Congenital_and_Developmental_Conditions)
- **Substring:** `deformit` (weight: 8.0)
- **Token:** `deformity` (weight: 8.0)
- **Problem:** Both will match "deformity", potentially adding 16 weight instead of 8
- **Recommendation:** Remove the substring entry; the token match is sufficient

---

## 2. SEMANTIC AMBIGUITIES 🔍

### 2.1 Cross-Lexicon Semantic Overlaps

#### Phthisis (Wasting Disease)
**Status:** AMBIGUOUS - appears in 2 lexicons with different contexts

- **L1_05_Chronic_Non-Communicable_Diseases:**
  - `phthisis` (weight: 7.0, token)
  - `phthisis (not def. as t.b.)` (weight: 8.0, phrase) - explicitly NOT tuberculosis
  
- **L1_06_Respiratory_and_Environmental_Disease:**
  - `phthisis (not otherwise def.)` (weight: 7.0, phrase) - undefined wasting

**Why problematic:** Historical term for consumption/wasting that could be either chronic disease or respiratory. The phrase qualifiers help, but the generic token "phthisis" in L1_05 could catch respiratory cases.

**Recommendation:** Remove the generic `phthisis` token from L1_05, keep only the qualified phrases.

---

#### Cirrhosis
**Status:** INTENTIONAL OVERLAP - alcohol-specific vs. general

- **L1_05_Chronic_Non-Communicable_Diseases:**
  - `cirrhosis` (weight: 7.0, token) - general liver disease
  
- **L1_09_Self-Harm_and_Substance_Use:**
  - `cirrhosis of liver (alcoholic)` (weight: 9.0, phrase) - specifically alcoholic

**Why problematic:** A death cause mentioning "cirrhosis of liver (alcoholic)" will score in BOTH categories (7 + 9 = 16 total), with substance use scoring higher. This appears intentional but could split classification if other terms are present.

**Recommendation:** Accept as designed feature. The more specific phrase gets higher weight, which is correct behavior.

---

#### Suicide Terms
**Status:** CRITICAL AMBIGUITY - same concept in two categories

- **L1_07_Injury_and_Accidental_Harm:**
  - `suicides` (weight: 9.0, token) - plural form
  
- **L1_09_Self-Harm_and_Substance_Use:**
  - `suicide` (weight: 9.0, token) - singular form
  - `self inflicted` (weight: 8.0, phrase)
  - `self harm` (weight: 9.0, phrase)

**Why problematic:** "Suicides" (plural) appears in Injury/Accidental category, while "suicide" (singular) is in Self-Harm. This seems like a classification error - suicide deaths should consistently be in Self-Harm, not split across categories.

**Recommendation:** **REMOVE** `suicides` from L1_07_Injury_and_Accidental_Harm. All suicide-related deaths should be classified under L1_09_Self-Harm_and_Substance_Use.

---

#### Pneumonia-Related Terms
**Status:** ACCEPTABLE - different aspects

- **L1_01_Infectious_and_Communicable_Diseases:**
  - `pneumococc` (weight: 8.0, substring) - bacterial organism causing pneumonia
  
- **L1_06_Respiratory_and_Environmental_Disease:**
  - `pneumonia` (weight: 7.0, token) - the disease itself

**Why problematic:** "Pneumococcal pneumonia" could score in both (8 + 7 = 15). However, this reflects reality - it's both an infectious disease AND a respiratory condition.

**Recommendation:** Accept as designed. This dual classification makes medical sense.

---

#### Heart Disease Terms
**Status:** MINOR OVERLAP - mostly distinct

- **L1_05_Chronic_Non-Communicable_Diseases:** 10 heart-related terms (various cardiac conditions)
- **L1_06_Respiratory_and_Environmental_Disease:** 
  - `fatty degeneration of heart` (weight: 7.0)

**Why problematic:** Very specific overlap - only one term crosses boundaries. "Fatty degeneration of heart" could be argued as either chronic disease or environmentally-related degeneration.

**Recommendation:** Accept as is, or consider moving to L1_05 for consistency.

---

#### Chronic Poisoning
**Status:** ACCEPTABLE - different contexts

- **L1_05_Chronic_Non-Communicable_Diseases:**
  - `chronic` (weight: 5.0, token) - general chronic disease indicator
  
- **L1_07_Injury_and_Accidental_Harm:**
  - `other chronic poisonings` (weight: 7.0, phrase) - specific poisoning type

**Why problematic:** The word "chronic" appears in both, but context differs significantly. The phrase match is more specific.

**Recommendation:** Accept as designed. The low weight (5.0) on generic "chronic" is appropriate.

---

#### Maternal/Puerperal Terms
**Status:** ACCEPTABLE - exclusion patterns working correctly

- **L1_02_Maternal_and_Early-Life_Mortality:**
  - `puerperal` (weight: 9.0, token)
  - `not puerperal` (weight: -50.0, phrase) - exclusion
  - `non-puerperal` (weight: -50.0, phrase) - exclusion
  
- **L1_05_Chronic_Non-Communicable_Diseases:**
  - `peritonitis (not puerperal)` (weight: 7.0, phrase)

**Why problematic:** Not really problematic - the exclusion pattern (-50 weight) in L1_02 will correctly prevent "peritonitis (not puerperal)" from being classified as maternal.

**Recommendation:** Accept as designed. Exclusion patterns are working correctly.

---

## 3. NEGATIVE WEIGHT EXCLUSION PATTERNS ✋

Three lexicons use negative weights to explicitly exclude certain cases:

### L1_01_Infectious_and_Communicable_Diseases
- `not infective` (weight: -50.0)
- `not diphtheritic` (weight: -50.0)
- `not returned as infective` (weight: -50.0)

### L1_02_Maternal_and_Early-Life_Mortality
- `not puerperal` (weight: -50.0)
- `non-puerperal` (weight: -50.0)
- `5yrs and over` (weight: -50.0)

### L1_06_Respiratory_and_Environmental_Disease
- `non-occupational` (weight: -50.0)

**Assessment:** These are well-designed exclusion patterns that prevent misclassification. The -50 weight is strong enough to override most positive matches.

---

## 4. REGEX PATTERNS ⚙️

Two regex patterns found in **L1_05_Chronic_Non-Communicable_Diseases**:

1. `Other diseases of .*` (weight: 7.0)
   - **Purpose:** Catch-all for chronic disease descriptions
   - **Risk:** Could match unintended phrases
   - **Example matches:** "Other diseases of bones", "Other diseases of joints", etc.

2. `disorders of .*` (weight: 6.0)
   - **Purpose:** Generic disorders pattern
   - **Risk:** Very broad, could match many phrases
   - **Example matches:** "disorders of metabolism", "disorders of circulation", etc.

**Recommendation:** Monitor these patterns carefully. Consider if more specific phrases would be better than regex wildcards.

---

## 5. WEIGHT DISTRIBUTION ANALYSIS

### High-Weight Terms (≥9.0) - Strong Indicators
- **L1_01 (Infectious):** 23 terms - specific diseases like tuberculosis, cholera, measles
- **L1_02 (Maternal):** 12 terms - puerperal, neonatal, stillbirth
- **L1_03 (Congenital):** 5 terms - congenital, spina bifida, cleft palate
- **L1_04 (Later-Life):** 3 terms - old age, senility, senile decay
- **L1_08 (Violence):** 3 terms - homicide, murder, execution
- **L1_09 (Self-Harm):** 4 terms - suicide, alcoholism, self harm
- **L1_10 (Ill-Defined):** 7 terms - cause unknown, found dead, sudden death

### Low-Weight Terms (≤5.0) - Weak Indicators
Only 7 terms total:
- `infection` (4.0), `infectious` (5.0) - appropriately weak generic terms
- `chronic` (5.0) - appropriately weak generic term
- `not specified` (4.0), `symptom` (5.0) - appropriately weak

**Assessment:** Weight distribution is well-designed. Specific medical terms get high weights (8-9), while generic terms get lower weights (4-5).

---

## 6. SUBSTRING MATCHES 🔤

13 substring patterns across lexicons:

### L1_01_Infectious_and_Communicable_Diseases (9 patterns)
- Bacterial organisms: `streptococc`, `staphylococc`, `pneumococc`, `mycobacter`, `clostrid`, `bordetella`
- Diseases: `ricketts`, `trypanosom`, `poliomyel`

### L1_02_Maternal_and_Early-Life_Mortality (1 pattern)
- `neonat` - ⚠️ **CONFLICT** with token "neonatal"

### L1_03_Congenital_and_Developmental_Conditions (1 pattern)
- `deformit` - ⚠️ **CONFLICT** with token "deformity"

### L1_09_Self-Harm_and_Substance_Use (1 pattern)
- `barbitur` - matches barbiturates, barbiturate, etc.

**Assessment:** Most substring patterns are well-chosen for capturing word variations. The two conflicts noted should be resolved.

---

## 7. RECOMMENDATIONS SUMMARY

### Priority 1: Fix Immediate Conflicts
1. ✅ **Remove duplicate substring/token pairs:**
   - Remove `neonat` substring from L1_02 (keep `neonatal` token)
   - Remove `deformit` substring from L1_03 (keep `deformity` token)

2. ✅ **Fix suicide classification split:**
   - Remove `suicides` from L1_07_Injury_and_Accidental_Harm
   - All suicide terms should only be in L1_09_Self-Harm_and_Substance_Use

### Priority 2: Clarify Ambiguities
3. ⚠️ **Clean up phthisis:**
   - Remove generic `phthisis` token from L1_05
   - Keep only qualified phrases that specify context

4. ⚠️ **Document cirrhosis behavior:**
   - Add note that alcoholic cirrhosis will score in both L1_05 and L1_09
   - This is intentional dual classification

### Priority 3: Monitor & Validate
5. 📊 **Test regex patterns:**
   - Validate `Other diseases of .*` and `disorders of .*` don't over-match
   - Consider replacing with specific phrase lists if too broad

6. 📊 **Review pneumonia overlap:**
   - Document that pneumococcal infections will score in both L1_01 and L1_06
   - Verify this is desired behavior for historical medical data

---

## 8. CONCLUSION

The lexicon system is **well-designed** with minimal critical conflicts. The main issues are:

1. **2 technical bugs** (substring/token duplicates) - easy fix
2. **1 classification error** (suicide split) - should be corrected
3. **Several intentional overlaps** (cirrhosis, pneumonia) - acceptable if documented

The use of negative weights for exclusions is sophisticated and appropriate. The weight distribution (4-9 range) provides good discrimination between weak and strong indicators.

**Overall Assessment:** ✅ **System is production-ready** after fixing the 3 priority issues above.

---

## Appendix: Files Analyzed

```
L1_01_Infectious_and_Communicable_Diseases.csv (44 terms)
L1_02_Maternal_and_Early-Life_Mortality.csv (28 terms)
L1_03_Congenital_and_Developmental_Conditions.csv (13 terms)
L1_04_Later-Life_Mortality.csv (5 terms)
L1_05_Chronic_Non-Communicable_Diseases.csv (109 terms)
L1_06_Respiratory_and_Environmental_Disease.csv (37 terms)
L1_07_Injury_and_Accidental_Harm.csv (25 terms)
L1_08_Violence_and_Conflict.csv (9 terms)
L1_09_Self-Harm_and_Substance_Use.csv (18 terms)
L1_10_Ill-Defined_Administrative_and_Other_Causes.csv (13 terms)
```

**Total:** 301 terms across 10 lexicons
