"""
Auto-writes Level-1 lexicon CSVs for the
ICD Socio-Economic Classification System.

Run once. Safe to re-run (overwrites files).
"""

import os
import pandas as pd

BASE_DIR = os.getcwd()
LEX_DIR = os.path.join(BASE_DIR, "lexicons")
os.makedirs(LEX_DIR, exist_ok=True)


def write_lexicon(filename, rows):
    df = pd.DataFrame(rows, columns=["term", "weight", "match_type", "source", "notes"])
    path = os.path.join(LEX_DIR, filename)
    df.to_csv(path, index=False)
    print(f"Wrote {path}")


# --------------------------------------------------
# L1_01 – Infectious and Communicable Diseases
# --------------------------------------------------

write_lexicon(
    "L1_01_Infectious_and_Communicable_Diseases.csv",
    [
        # Core disease terms
        ("infection", 4, "token", "core", ""),
        ("infectious", 5, "token", "core", ""),
        ("epidemic", 6, "token", "core", ""),
        ("pandemic", 6, "token", "core", ""),
        ("contagious", 6, "token", "core", ""),
        ("communicable", 6, "token", "core", ""),

        # Organisms / families
        ("streptococc", 8, "substring", "organism", ""),
        ("staphylococc", 8, "substring", "organism", ""),
        ("pneumococc", 8, "substring", "organism", ""),
        ("mycobacter", 9, "substring", "organism", ""),
        ("clostrid", 8, "substring", "organism", ""),
        ("bordetella", 9, "substring", "organism", ""),
        ("ricketts", 9, "substring", "organism", ""),
        ("listeria", 8, "token", "organism", ""),

        # Named infections
        ("tuberculosis", 9, "token", "disease", ""),
        ("typhus", 8, "token", "disease", ""),
        ("cholera", 9, "token", "disease", ""),
        ("diphtheria", 9, "token", "disease", ""),
        ("tetanus", 9, "token", "disease", ""),
        ("plague", 9, "token", "disease", ""),
        ("smallpox", 9, "token", "disease", ""),
        ("variola", 9, "token", "disease", ""),
        ("measles", 9, "token", "disease", ""),
        ("rubella", 9, "token", "disease", ""),
        ("mumps", 9, "token", "disease", ""),
        ("whooping cough", 9, "phrase", "disease", ""),
        ("pertussis", 9, "token", "disease", ""),
        ("erysipelas", 8, "token", "disease", ""),
        ("septicaemia", 8, "token", "disease", ""),
        ("septicemia", 8, "token", "disease", ""),
        ("pyaemia", 8, "token", "disease", ""),
        ("malaria", 9, "token", "disease", ""),
        ("leishmaniasis", 9, "token", "disease", ""),
        ("trypanosom", 9, "substring", "disease", ""),
        ("rabies", 9, "token", "disease", ""),
        ("yellow fever", 9, "phrase", "disease", ""),
        ("haemorrhagic fever", 9, "phrase", "disease", ""),
        ("arthropod borne", 8, "phrase", "vector", ""),
        ("venereal", 7, "token", "transmission", ""),
    ],
)


# --------------------------------------------------
# L1_02 – Maternal and Early-Life Mortality
# --------------------------------------------------

write_lexicon(
    "L1_02_Maternal_and_Early-Life_Mortality.csv",
    [
        ("maternal", 7, "token", "core", ""),
        ("puerperal", 9, "token", "core", ""),
        ("pregnancy", 8, "token", "core", ""),
        ("childbirth", 8, "token", "core", ""),
        ("delivery", 8, "token", "core", ""),
        ("abortion", 8, "token", "core", ""),
        ("ectopic", 8, "token", "core", ""),
        ("stillbirth", 9, "token", "core", ""),
        ("newborn", 9, "token", "core", ""),
        ("neonatal", 9, "token", "core", ""),
        ("infancy", 8, "token", "core", ""),
        ("immaturity", 9, "token", "core", ""),
        ("at birth", 9, "phrase", "core", ""),
        ("early infancy", 9, "phrase", "core", ""),
    ],
)


# --------------------------------------------------
# L1_03 – Congenital and Developmental Conditions
# --------------------------------------------------

write_lexicon(
    "L1_03_Congenital_and_Developmental_Conditions.csv",
    [
        ("congenital", 9, "token", "core", ""),
        ("malformation", 8, "token", "core", ""),
        ("deformity", 8, "token", "core", ""),
        ("deformit", 8, "substring", "core", ""),
        ("spina bifida", 9, "phrase", "condition", ""),
        ("cleft palate", 9, "phrase", "condition", ""),
        ("harelip", 9, "token", "condition", ""),
        ("clubfoot", 9, "token", "condition", ""),
        ("hydrocephalus", 8, "token", "condition", ""),
        ("haemophilia", 8, "token", "genetic", ""),
    ],
)


# --------------------------------------------------
# L1_04 – Later-Life Mortality
# --------------------------------------------------

write_lexicon(
    "L1_04_Later-Life_Mortality.csv",
    [
        ("old age", 9, "phrase", "core", ""),
        ("senility", 9, "token", "core", ""),
        ("senile", 8, "token", "core", ""),
        ("senile decay", 9, "phrase", "core", ""),
        ("age related", 7, "phrase", "core", ""),
    ],
)


# --------------------------------------------------
# L1_05 – Chronic Non-Communicable Diseases
# --------------------------------------------------

write_lexicon(
    "L1_05_Chronic_Non-Communicable_Diseases.csv",
    [
        ("chronic", 5, "token", "core", ""),
        ("degeneration", 6, "token", "core", ""),
        ("carcinoma", 8, "token", "disease", ""),
        ("cancer", 8, "token", "disease", ""),
        ("sarcoma", 8, "token", "disease", ""),
        ("diabetes", 8, "token", "disease", ""),
        ("cirrhosis", 7, "token", "disease", ""),
        ("arthritis", 6, "token", "disease", ""),
        ("gout", 6, "token", "disease", ""),
    ],
)


# --------------------------------------------------
# L1_06 – Respiratory and Environmental Disease
# --------------------------------------------------

write_lexicon(
    "L1_06_Respiratory_and_Environmental_Disease.csv",
    [
        ("respiratory", 6, "token", "core", ""),
        ("pneumonia", 7, "token", "disease", ""),
        ("bronchitis", 7, "token", "disease", ""),
        ("asthma", 6, "token", "disease", ""),
        ("emphysema", 7, "token", "disease", ""),
        ("occupational", 7, "token", "environmental", ""),
        ("industrial", 7, "token", "environmental", ""),
        ("dust", 6, "token", "environmental", ""),
        ("smoke", 6, "token", "environmental", ""),
    ],
)


# --------------------------------------------------
# L1_07 – Injury and Accidental Harm
# --------------------------------------------------

write_lexicon(
    "L1_07_Injury_and_Accidental_Harm.csv",
    [
        ("accident", 7, "token", "core", ""),
        ("injury", 7, "token", "core", ""),
        ("fracture", 7, "token", "core", ""),
        ("fall", 7, "token", "core", ""),
        ("burn", 7, "token", "core", ""),
        ("scald", 7, "token", "core", ""),
        ("drowning", 7, "token", "core", ""),
        ("railway", 6, "token", "context", ""),
        ("machinery", 6, "token", "context", ""),
    ],
)


# --------------------------------------------------
# L1_08 – Violence and Conflict
# --------------------------------------------------

write_lexicon(
    "L1_08_Violence_and_Conflict.csv",
    [
        ("violence", 8, "token", "core", ""),
        ("homicide", 9, "token", "core", ""),
        ("murder", 9, "token", "core", ""),
        ("assault", 8, "token", "core", ""),
        ("war", 8, "token", "core", ""),
        ("battle", 8, "token", "core", ""),
        ("execution", 9, "token", "core", ""),
        ("killed by", 8, "phrase", "core", ""),
    ],
)


# --------------------------------------------------
# L1_09 – Self-Harm and Substance Use
# --------------------------------------------------

write_lexicon(
    "L1_09_Self-Harm_and_Substance_Use.csv",
    [
        ("suicide", 9, "token", "core", ""),
        ("self inflicted", 8, "phrase", "core", ""),
        ("addiction", 8, "token", "substance", ""),
        ("dependence", 8, "token", "substance", ""),
        ("alcoholism", 9, "token", "substance", ""),
        ("drug", 6, "token", "substance", ""),
        ("morphine", 8, "token", "substance", ""),
        ("opium", 8, "token", "substance", ""),
        ("barbitur", 8, "substring", "substance", ""),
        ("cocaine", 8, "token", "substance", ""),
        ("amphetamine", 8, "token", "substance", ""),
        ("mdma", 8, "token", "substance", ""),
        ("cannabis", 8, "token", "substance", ""),
        ("tobacco", 7, "token", "substance", ""),
        ("nicotine", 7, "token", "substance", ""),
    ],
)


# --------------------------------------------------
# L1_10 – Ill-Defined, Administrative, Other
# --------------------------------------------------

write_lexicon(
    "L1_10_Ill-Defined_Administrative_and_Other_Causes.csv",
    [
        ("ill defined", 8, "phrase", "core", ""),
        ("cause unknown", 9, "phrase", "core", ""),
        ("unknown cause", 9, "phrase", "core", ""),
        ("found dead", 9, "phrase", "core", ""),
        ("not specified", 4, "phrase", "weak", ""),
        ("observation", 7, "token", "admin", ""),
        ("symptom", 5, "token", "admin", ""),
    ],
)

print("\nAll lexicons written successfully.")
