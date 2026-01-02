content = """ICD Canonical Classification Logic (v1.0)
=================================

This document captures the *decision model* used to classify historical ICD codes
(ICD-1 through ICD-6) into the locked Level-1 Socio-Economic Mortality Taxonomy.

This is **logic**, not a lookup table. Numeric ranges are used only as guardrails
where ICD structure is explicit; semantic rules always take precedence.

--------------------------------------------------
LOCKED LEVEL-1 CATEGORIES
--------------------------------------------------
L1_01 Infectious and Communicable Diseases
L1_02 Maternal and Early-Life Mortality
L1_03 Congenital and Developmental Conditions
L1_04 Later-Life Mortality
L1_05 Chronic Non-Communicable Diseases
L1_06 Respiratory and Environmental Disease
L1_07 Injury and Accidental Harm
L1_08 Violence and Conflict
L1_09 Self-Harm and Substance Use
L1_10 Ill-Defined, Administrative, and Other Causes

--------------------------------------------------
CORE PRINCIPLES (ORDER MATTERS)
--------------------------------------------------

1. **Life-stage beats pathology**
   Neonatal / perinatal context overrides infectious, respiratory, or injury wording.

2. **Domain certainty beats intent**
   Poisoning, violence, or occupational exposure is classified by domain even if
   intent (accidental vs deliberate) is unclear.

3. **Ill-defined ≠ early life**
   Early-infancy diagnostic limits are *not* administrative uncertainty.

4. **Environment includes nutrition and work**
   Nutritional deficiency and occupational disease are environmental unless violent
   or accidental.

--------------------------------------------------
PRIMARY SEMANTIC RULES
--------------------------------------------------

MATERNAL & EARLY-LIFE (L1_02)
Trigger if description contains:
- newborn / neonatal / infancy / immaturity
- at birth / birth injury / delivery / labour / childbirth
- puerperal / postpartum / intrapartum / obstetric
- haemolytic disease of newborn / erythroblastosis / kernicterus
- ophthalmia neonatorum / pemphigus neonatorum / umbilical sepsis

Also includes:
- all neonatal infections
- perinatal respiratory failure
- immaturity / prematurity (qualified or unqualified)

--------------------------------------------------

CONGENITAL & DEVELOPMENTAL (L1_03)
Trigger if description contains:
- congenital / malformation / deformity
- spina bifida / meningocele
- cleft palate / harelip
- clubfoot / flat foot / hallux valgus / curvature of spine
- haemophilia / cretinism / monstrosity

Structural deformities default here unless explicitly traumatic.

--------------------------------------------------

INFECTIOUS & COMMUNICABLE (L1_01)
Trigger if description contains:
- tuberculosis / tubercle / phthisis
- meningitis / encephalitis
- syphilis / gonorrhoeal / ophthalmia
- septicaemia / pyaemia / tetanus / anthrax / rabies
- osteomyelitis / periostitis
- epidemic / plague / cholera / influenza

--------------------------------------------------

ENVIRONMENTAL (L1_06)
Includes:
- nutritional deficiency (rickets, scurvy, pellagra, vitamin deficiency)
- dehydration / starvation / weight loss
- occupational disease (non-accidental, non-violent)
- environmental exposure (heat, cold, air, housing)

--------------------------------------------------

INJURY & ACCIDENTAL HARM (L1_07)
Includes:
- transport accidents
- falls
- industrial accidents
- accidental poisonings
- medical / therapeutic misadventure
- foreign bodies / venomous animals

Excludes:
- birth injuries
- interpersonal violence

--------------------------------------------------

VIOLENCE & CONFLICT (L1_08)
Includes:
- homicide
- execution
- war / battle
- firearm injury (even if described as accidental)
- violence by another person

--------------------------------------------------

SELF-HARM & SUBSTANCE USE (L1_09)
Includes:
- suicide (any method)
- alcohol poisoning
- narcotics / soporifics poisoning
- unspecified poisoning where intent unclear but domain is substance

--------------------------------------------------

ILL-DEFINED / ADMINISTRATIVE (L1_10)
Includes:
- rash
- subcutaneous nodules
- tetany / acidosis / alkalosis
- pyrexia of unknown origin
- debility / undue fatigue
- observation without need for medical care
- cause unknown / not specified / unstated

--------------------------------------------------
ICD-6 STRUCTURAL GUARDRAILS
--------------------------------------------------
(Used only where ICD-6 structure is explicit)

6600–6790  Delivery → L1_02
7600–7799  Neonatal conditions → L1_02
8000–8699  Accidents → L1_07
8700–8999  Accidental poisoning → L1_07
9000–9189  Accidents / falls → L1_07
9190–9199  Firearms → L1_08
9300–9359  Environmental exposure → L1_06
9400–9599  Iatrogenic → L1_07
9800–9999  Violence → L1_08

--------------------------------------------------
CONFIDENCE ASSIGNMENT
--------------------------------------------------
High:
- Explicit domain (neonatal, congenital, accident, violence)

Medium:
- Domain clear, intent unclear

Low:
- Administrative / symptom-only / observational entries

--------------------------------------------------
END OF LOGIC
--------------------------------------------------
"""

path = "/mnt/data/icd_classification_logic.txt"
with open(path, "w", encoding="utf-8") as f:
    f.write(content)

path
