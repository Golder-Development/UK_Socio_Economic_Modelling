"""
Create a harmonized/standardized classification system for mortality causes across all ICD versions.
This enables longitudinal analysis by mapping all codes to consistent categories.

Strategy:
- Create broad disease categories that work across all ICD versions (1901-2000)
- Map specific codes from each ICD version to these standard categories
- Accept that some granularity will be lost for comparability
- Document which specific conditions only appear in later periods
"""

import pandas as pd
from pathlib import Path
import logging
import re

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent
PARENT_DIR = DATA_DIR.parent

# Define harmonized disease categories based on broad ICD chapter-like groupings
# These are designed to be stable across 1901-2000
HARMONIZED_CATEGORIES = {
    "infectious_diseases": {
        "name": "Infectious and Parasitic Diseases",
        "keywords": [
            "fever",
            "pox",
            "plague",
            "cholera",
            "typhus",
            "typhoid",
            "malaria",
            "diphtheria",
            "whooping",
            "scarlet",
            "measles",
            "influenza",
            "tuberculosis",
            "septic",
            "infection",
            "tetanus",
            "anthrax",
            "rabies",
            "syphilis",
            "gonorrhoea",
            "dysentery",
            "enteritis",
            "diarrhoea",
            "polio",
            "encephalitis",
            "meningitis",
            "leprosy",
            "mumps",
            "rubella",
            "pertussis",
            "streptococcal",
            "staphylococcal",
            "pneumococcal",
            "viral",
            "bacterial",
            "parasit",
            "helminth",
            "fungal",
            "infectious disease",
            "epidemic",
            "endemic",
            "varicella",
            "glanders",
            "antinomycosis",
            "other mycosis",
            "trematodes",
            "disease due to nematodes",
            "disease due to trematodes",
            "disease due to coccidia",
        ],
    },
    "neoplasms": {
        "name": "Neoplasms (Cancers and Tumors)",
        "keywords": [
            "cancer",
            "carcinoma",
            "sarcoma",
            "tumor",
            "tumour",
            "neoplasm",
            "malignant",
            "benign",
            "lymphoma",
            "leukaemia",
            "leukemia",
            "melanoma",
            "adenoma",
            "adenocarcinoma",
            "glioma",
            "metasta",
        ],
    },
    "blood_immune": {
        "name": "Blood and Immune System Disorders",
        "keywords": [
            "anaemia",
            "anemia",
            "haemophilia",
            "purpura",
            "thrombocytopeni",
            "agranulocytosis",
            "immunodeficiency",
            "immune disorder",
            "thymus",
            "diseases of the thymus",
            "diseases of the spleen",
            "disseminated sclerosis",
            "multiple sclerosis",
            "pemphigus",
        ],
    },
    "endocrine_metabolic": {
        "name": "Endocrine, Nutritional and Metabolic Diseases",
        "keywords": [
            "diabetes",
            "thyroid",
            "goitre",
            "gout",
            "rickets",
            "scurvy",
            "beriberi",
            "pellagra",
            "marasmus",
            "kwashiorkor",
            "malnutrition",
            "obesity",
            "vitamin deficiency",
            "metabolic",
            "addison",
            "cushing",
            "acromegaly",
            "pituitary",
        ],
    },
    "mental_behavioral": {
        "name": "Mental and Behavioral Disorders",
        "keywords": [
            "mental",
            "insanity",
            "mania",
            "melancholia",
            "psychosis",
            "neurosis",
            "dementia",
            "delirium",
            "schizophrenia",
            "depression",
            "anxiety",
            "intellectual disability",
            "idiocy,imbecility"
        ],
    },
    "nervous_system": {
        "name": "Diseases of the Nervous System",
        "keywords": [
            "nervous",
            "brain",
            "cerebral",
            "apoplexy",
            "paralysis",
            "hemiplegia",
            "epilepsy",
            "convulsion",
            "meningitis",
            "encephalitis",
            "parkinson",
            "multiple sclerosis",
            "neuralgia",
            "neuritis",
            "migraine",
            "headache",
            "beri-beri",
            "tetany",
            "tabes dorsalis",
            "locomotor ataxia",
            "chorea",
        ],
    },
    "eye_ear": {
        "name": "Diseases of Eye and Ear",
        "keywords": [
            "eye",
            "vision",
            "blind",
            "cataract",
            "glaucoma",
            "ear",
            "deaf",
            "otitis",
            "mastoid sinus",
            "mastoiditis",
        ],
    },
    "circulatory": {
        "name": "Diseases of the Circulatory System",
        "keywords": [
            "heart",
            "cardiac",
            "myocardi",
            "endocardi",
            "pericardi",
            "angina",
            "coronary",
            "artery",
            "arteriosclerosis",
            "atherosclerosis",
            "hypertension",
            "stroke",
            "cerebrovascular",
            "haemorrhage",
            "hemorrhage",
            "embolism",
            "thrombosis",
            "aneurysm",
            "varicose",
            "phlebitis",
            "gangrene",
            "vascular",
            "aortic valve disease",
            "mitral valve disease",
            "aortic and mitral valve disease",
            "other diseases of the arteries",
            "other diseases of the circulatory system",
        ],
    },
    "respiratory": {
        "name": "Diseases of the Respiratory System",
        "keywords": [
            "lung",
            "pulmonary",
            "bronch",
            "pneumonia",
            "asthma",
            "emphysema",
            "larynx",
            "laryngitis",
            "croup",
            "pharynx",
            "tonsil",
            "respiratory",
            "pleurisy",
            "pleural",
            "pneumothorax",
            "silicosis",
            "asbestosis",
            "diseases of the nose",
            "diseases of the accessory nasal sinuses",
            "laryngismus stridulus",
            "empyema",
            "atelectasis",
        ],
    },
    "digestive": {
        "name": "Diseases of the Digestive System",
        "keywords": [
            "stomach",
            "gastric",
            "gastritis",
            "ulcer",
            "intestin",
            "bowel",
            "colon",
            "rectum",
            "anus",
            "appendicitis",
            "peritonitis",
            "hernia",
            "liver",
            "hepat",
            "cirrhosis",
            "gallbladder",
            "cholecyst",
            "pancrea",
            "oesophag",
            "esophag",
            "digestive",
            "alimentary",
            "spirochaetosis",
            "colitis",
            "ankylostomiasis",
            "biliary calculi",
        ],
    },
    "skin": {
        "name": "Diseases of the Skin",
        "keywords": [
            "skin",
            "dermat",
            "eczema",
            "psoriasis",
            "ulcer",
            "abscess",
            "carbuncle",
            "cellulitis",
            "gangrene",
            "erysipelas",
            "myxoedema",
        ],
    },
    "musculoskeletal": {
        "name": "Diseases of Musculoskeletal System and Connective Tissue",
        "keywords": [
            "arthritis",
            "rheumat",
            "osteo",
            "bone",
            "joint",
            "muscle",
            "muscular",
            "spine",
            "spinal",
            "scoliosis",
            "dorsopathy",
        ],
    },
    "genitourinary": {
        "name": "Diseases of the Genitourinary System",
        "keywords": [
            "kidney",
            "renal",
            "nephri",
            "urinary",
            "bladder",
            "cystitis",
            "urethr",
            "prostate",
            "uterus",
            "ovary",
            "vagina",
            "menstrual",
            "genital",
            "soft chancre",
            "chancroid",
            "chyluria",
            "salpingitis",
        ],
    },
    "pregnancy_childbirth": {
        "name": "Pregnancy, Childbirth and Puerperium",
        "keywords": [
            "pregnancy",
            "pregnant",
            "childbirth",
            "labour",
            "labor",
            "delivery",
            "puerperal",
            "placenta",
            "abortion",
            "miscarriage",
            "ectopic",
            "obstetric",
            "icterus neonatorum",
            "diseases of the umbilicus",
        ],
    },
    "perinatal": {
        "name": "Conditions Originating in Perinatal Period",
        "keywords": [
            "newborn",
            "neonatal",
            "birth",
            "prematurity",
            "foetal",
            "fetal",
            "perinatal",
            "congenital",
            "cretinism",
            "congenital hypothyroidism",
        ],
    },
    "congenital": {
        "name": "Congenital Malformations and Chromosomal Abnormalities",
        "keywords": [
            "congenital",
            "malformation",
            "deformity",
            "chromosomal",
            "down syndrome",
            "spina bifida",
            "cleft",
        ],
    },
    "injury_poisoning": {
        "name": "Injury, Poisoning and External Causes",
        "keywords": [
            "injury",
            "trauma",
            "wound",
            "fracture",
            "burn",
            "poison",
            "toxic",
            "drown",
            "suffocation",
            "fall",
            "crush",
            "motor vehicle",
            "railway",
            "fire",
            "vaccinia*",
        ],
    },
    "Suicide": {
        "name": "Suicide and Self-Inflicted Injury",
        "keywords": [
            "suicide",
        ],
    },
    "Accident": {
        "name": "Accidental Death",
        "keywords": [
            "accident",
            "conflagration",
            "lightening",
            "electricity",
        ],
    },
    "Homicide": {
        "name": "Homicide and Assault",
        "keywords": [
            "homicide",
            "violence",
            "assault",
            "weapon",
        ],
    },
    "Legal Drugs": {
        "name": "Legal Drug-Related Deaths",
        "keywords": [
            "tobacco",
            "alcohol",
            "alcohol dependence syndrome",
            "alcoholism",
            "alcoholic psychoses",
        ],
    },
    "Drugs": {
        "name": "Drug-Related Deaths",
        "keywords": [
            "overdose",
            "drug dependence",
            'opium',
            "drug psychoses",
            "nonedependent abuse of drugs"
        ],
    },
    "War": {
        "name": "War and War-Related Deaths",
        "keywords": [
            "battle",
            "war ",
            "executions of civilians by belligerent armies"
        ],
    },
    "ill_defined": {
        "name": "Symptoms, Signs and Ill-Defined Conditions",
        "keywords": [
            "symptom",
            "sign",
            "ill-defined",
            "unknown",
            "unspecified",
            "senility",
            "old age",
            "debility",
            "sudden death",
            "found dead",
        ],
    },
    "other": {
        "name": "Other and Unclassified",
        "keywords": [],  # Catch-all for anything that doesn't match
    },
}


def classify_by_keywords(description, code=None):
    """
    Classify a disease description into harmonized category based on keywords.
    Returns tuple: (category_id, category_name, confidence)
    """
    if not description or pd.isna(description):
        return ("ill_defined", "Symptoms, Signs and Ill-Defined Conditions", "unknown")

    description_lower = str(description).lower()

    # Check each category's keywords
    matches = []
    for cat_id, cat_info in HARMONIZED_CATEGORIES.items():
        if cat_id == "other":  # Skip the catch-all for now
            continue

        match_count = 0
        for keyword in cat_info["keywords"]:
            if keyword.lower() in description_lower:
                match_count += 1

        if match_count > 0:
            matches.append((cat_id, cat_info["name"], match_count))

    if matches:
        # Return the category with most keyword matches
        matches.sort(key=lambda x: x[2], reverse=True)
        best_match = matches[0]
        confidence = "high" if best_match[2] >= 2 else "medium"
        return (best_match[0], best_match[1], confidence)

    # No matches found, use catch-all
    return ("other", "Other and Unclassified", "low")


def build_harmonized_mapping():
    """
    Build a harmonized mapping for all ICD codes across all versions.
    """
    logger.info("=" * 80)
    logger.info("BUILDING HARMONIZED DISEASE CLASSIFICATION SYSTEM")
    logger.info("=" * 80)

    # Load the full descriptions file (prefer local, fallback to parent folder)
    desc_file = DATA_DIR / "icd_code_descriptions.csv"
    if not desc_file.exists():
        fallback = PARENT_DIR / "icd_code_descriptions.csv"
        if fallback.exists():
            logger.info("Using fallback descriptions from parent folder: icd_code_descriptions.csv")
            desc_file = fallback
        else:
            logger.error(
                "icd_code_descriptions.csv not found in development_code or parent folder. Run build_code_descriptions.py first."
            )
            return None

    logger.info(f"\nLoading ICD code descriptions...")
    descriptions_df = pd.read_csv(desc_file)
    logger.info(f"Loaded {len(descriptions_df):,} code descriptions")

    # Classify each code
    logger.info(
        f"\nClassifying codes into {len(HARMONIZED_CATEGORIES)} harmonized categories..."
    )

    results = []
    for _, row in descriptions_df.iterrows():
        cat_id, cat_name, confidence = classify_by_keywords(
            row["description"], row["code"]
        )
        results.append(
            {
                "code": row["code"],
                "icd_version": row["icd_version"],
                "original_description": row["description"],
                "harmonized_category": cat_id,
                "harmonized_category_name": cat_name,
                "classification_confidence": confidence,
            }
        )

    harmonized_df = pd.DataFrame(results)

    # Print statistics
    logger.info(f"\n{'=' * 80}")
    logger.info("CLASSIFICATION STATISTICS")
    logger.info("=" * 80)

    logger.info(f"\nDistribution across harmonized categories:")
    cat_counts = harmonized_df["harmonized_category_name"].value_counts()
    for cat, count in cat_counts.items():
        pct = count / len(harmonized_df) * 100
        logger.info(f"  {cat:50s}: {count:6,} ({pct:5.1f}%)")

    logger.info(f"\nClassification confidence levels:")
    conf_counts = harmonized_df["classification_confidence"].value_counts()
    for conf, count in conf_counts.items():
        pct = count / len(harmonized_df) * 100
        logger.info(f"  {conf:10s}: {count:6,} ({pct:5.1f}%)")

    # Show examples from each category
    logger.info(f"\n{'=' * 80}")
    logger.info("EXAMPLE CLASSIFICATIONS")
    logger.info("=" * 80)

    for cat_id, cat_info in list(HARMONIZED_CATEGORIES.items())[:5]:
        logger.info(f"\n{cat_info['name']}:")
        examples = harmonized_df[harmonized_df["harmonized_category"] == cat_id].head(3)
        for _, ex in examples.iterrows():
            logger.info(
                f"  {ex['icd_version']:20s} Code {ex['code']:10s}: {ex['original_description']}"
            )

    return harmonized_df


def save_harmonized_mapping(harmonized_df):
    """Save the harmonized mapping to CSV"""
    output_file = DATA_DIR / "icd_harmonized_categories.csv"
    harmonized_df.to_csv(output_file, index=False)
    logger.info(f"\n✓ Saved harmonized mapping to: {output_file}")

    # Also save to parent folder so downstream scripts loading from parent see latest mapping
    parent_output = DATA_DIR.parent / "icd_harmonized_categories.csv"
    try:
        harmonized_df.to_csv(parent_output, index=False)
        logger.info(f"✓ Saved harmonized mapping to: {parent_output}")
    except Exception as e:
        logger.warning(f"Could not write parent mapping file: {e}")

    # Also create a summary of categories
    summary_file = DATA_DIR / "harmonized_categories_summary.csv"
    summary_data = []
    for cat_id, cat_info in HARMONIZED_CATEGORIES.items():
        count = len(harmonized_df[harmonized_df["harmonized_category"] == cat_id])
        summary_data.append(
            {
                "category_id": cat_id,
                "category_name": cat_info["name"],
                "code_count": count,
                "example_keywords": ", ".join(cat_info["keywords"][:10]),
            }
        )

    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(summary_file, index=False)
    logger.info(f"✓ Saved category summary to: {summary_file}")


def main():
    harmonized_df = build_harmonized_mapping()

    if harmonized_df is not None:
        save_harmonized_mapping(harmonized_df)

        logger.info(f"\n{'=' * 80}")
        logger.info("COMPLETE")
        logger.info("=" * 80)
        logger.info("\nNext steps:")
        logger.info(
            "1. Review the harmonized categories in 'icd_harmonized_categories.csv'"
        )
        logger.info("2. Adjust keyword matching if needed")
        logger.info(
            "3. Run 'add_harmonized_categories_to_mortality.py' to add to mortality data"
        )


if __name__ == "__main__":
    main()
