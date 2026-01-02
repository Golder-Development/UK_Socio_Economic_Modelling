"""
Classification Engine Settings
-------------------------------

Domain-specific configuration for the lexicon-based classification engine.
Modify this file to adapt the engine to different classification tasks.

This file contains:
- Taxonomy definitions (categories, codes, names)
- Hard override rules
- File paths and column mappings
- Confidence thresholds
"""

from typing import Dict, List, Tuple


# ============================================================
# TAXONOMY DEFINITION
# ============================================================

# Primary taxonomy: maps category codes to human-readable names
# Edit this to define your own classification categories
TAXONOMY: Dict[str, str] = {
    "L1_01": "Infectious and Communicable Diseases",
    "L1_02": "Maternal and Early-Life Mortality",
    "L1_03": "Congenital and Developmental Conditions",
    "L1_04": "Later-Life Mortality",
    "L1_05": "Chronic Non-Communicable Diseases",
    "L1_06": "Respiratory and Environmental Disease",
    "L1_07": "Injury and Accidental Harm",
    "L1_08": "Violence and Conflict",
    "L1_09": "Self-Harm and Substance Use",
    "L1_10": "Ill-Defined, Administrative, and Other Causes",
}


# ============================================================
# HARD OVERRIDES
# ============================================================

# Hard overrides are structural rules that guarantee classification
# regardless of lexicon scores. Format:
# {
#     "category_code": [
#         ("pattern", "match_type"),
#         ...
#     ]
# }
# 
# match_type can be: "token", "phrase", "substring", "regex"

# All hard override terms have been added to their respective lexicons
# with high weights (8-9). Commenting out to use pure scoring.

# HARD_OVERRIDES: Dict[str, List[Tuple[str, str]]] = {
#     "L1_02": [
#         ("puerperal", "token"),
#         ("pregnancy", "token"),
#         ("childbirth", "token"),
#         ("delivery", "token"),
#         ("abortion", "token"),
#         ("ectopic", "token"),
#         ("newborn", "token"),
#         ("neonat", "substring"),
#         ("immaturity", "token"),
#         ("at birth", "phrase"),
#         ("early infancy", "phrase"),
#     ],
#     "L1_03": [
#         ("congenital", "token"),
#         ("malformation", "token"),
#         ("deformit", "substring"),
#         ("spina bifida", "phrase"),
#         ("cleft palate", "phrase"),
#         ("harelip", "token"),
#         ("clubfoot", "token"),
#         ("haemophilia", "token"),
#     ],
#     "L1_08": [
#         ("homicide", "token"),
#         ("murder", "token"),
#         ("execution", "token"),
#         ("war", "token"),
#         ("battle", "token"),
#         ("assault", "token"),
#     ],
#     "L1_09": [
#         ("suicide", "token"),
#         ("self harm", "phrase"),
#     ],
#     "L1_01": [
#         # infectious organism anchors
#         ("streptococc", "substring"),
#         ("staphylococc", "substring"),
#         ("pneumococc", "substring"),
#         ("mycobacter", "substring"),
#         ("clostrid", "substring"),
#         ("bordetella", "substring"),
#         ("variola", "token"),
#         ("poliomyel", "substring"),
#         ("ricketts", "substring"),
#         ("trypanosom", "substring"),
#         ("leishmaniasis", "token"),
#         ("malaria", "token"),
#         ("yellow fever", "phrase"),
#         ("infectious hepatitis", "phrase"),
#         ("haemorrhagic fever", "phrase"),
#         ("arthropod borne", "phrase"),
#         ("venereal", "token"),
#     ],
#     "L1_10": [
#         ("cause unknown", "phrase"),
#         ("found dead", "phrase"),
#         ("observation without need for further medical care", "phrase"),
#         ("pyrexia of unknown origin", "phrase"),
#     ],
# }

HARD_OVERRIDES: Dict[str, List[Tuple[str, str]]] = {}

# Optional: exclusions that suppress hard overrides when present.
# Format: {"category_code": [("pattern", "match_type"), ...]}
# HARD_OVERRIDE_EXCLUSIONS: Dict[str, List[Tuple[str, str]]] = {
#     "L1_02": [
#         ("not puerperal", "phrase"),
#     ],
#     "L1_01": [
#         ("not infective", "phrase"),
#     ],
# }

HARD_OVERRIDE_EXCLUSIONS: Dict[str, List[Tuple[str, str]]] = {}



# ============================================================
# CLASSIFICATION ORDER
# ============================================================

# Order in which hard overrides are checked (highest priority first)
# Only relevant if multiple overrides could match
OVERRIDE_PRIORITY: List[str] = []

'''
OVERRIDE_PRIORITY: List[str] = [
    "L1_02",  # Maternal/Early-Life
    "L1_03",  # Congenital
    "L1_08",  # Violence
    "L1_09",  # Self-Harm
    "L1_04",  # Later-Life
    "L1_06",  # Respiratory/Environmental
    "L1_01",  # Infectious
    "L1_05",  # Chronic NCDs
    "L1_10",  # Ill-Defined
]
'''

# ============================================================
# CONFIDENCE THRESHOLDS
# ============================================================

# Thresholds for assigning confidence levels
# Adjust based on your data characteristics

CONFIDENCE_THRESHOLDS = {
    "hard_override_score": 999,  # Score assigned when hard override triggers

    # High confidence
    "high_min_score": 18,
    "high_min_margin": 6,

    # Medium confidence
    "medium_min_score": 10,
    "medium_min_margin": 3,
}


# ============================================================
# INPUT DATA CONFIGURATION
# ============================================================

# Column mappings for input CSV
# Maps expected column names to possible variations in your data

INPUT_COLUMNS = {
    "code": ["code", "icd_code", "icdcode", "id", "classification_code"],
    "description": ["description", "desc", "text", "label", "name"],
    "version": ["version", "icd_version", "revision", "source"],
}


# Default column names if none found
DEFAULT_COLUMNS = {
    "code": "code",
    "description": "description",
    "version": "version",
}


# Fallback version name if no version column exists
DEFAULT_VERSION = "UNK"


# ============================================================
# OUTPUT CONFIGURATION
# ============================================================

# Output column names
OUTPUT_COLUMNS = {
    "version": "version",
    "code": "code",
    "description": "description",
    "category_code": "category_code",
    "category_name": "category_name",
    "confidence": "classification_confidence",
}


# ============================================================
# FILE PATHS
# ============================================================

# Default file locations (can be overridden via CLI arguments)

DEFAULT_PATHS = {
    "lexicon_dir": "lexicons",
    "input_csv": "data/input.csv",
    "output_csv": "output/classified.csv",
}


# ============================================================
# LEXICON CONFIGURATION
# ============================================================

# Expected lexicon file schema
LEXICON_SCHEMA = {
    "term_column": "term",
    "weight_column": "weight",
    "match_type_column": "match_type",
    "source_column": "source",      # optional
    "notes_column": "notes",        # optional
}


# Lexicon file naming pattern
# The pattern should contain a capture group for the category code
LEXICON_FILE_PATTERN = r"(L1_\d{2})"


# Valid match types in lexicons
VALID_MATCH_TYPES = ["token", "phrase", "substring", "regex"]

# Token matching options
TOKEN_MATCH_OPTIONS = {
    "enable_plural_variants": True,  # Match simple plural/singular variants for token terms
}


# ============================================================
# TEXT PROCESSING
# ============================================================

# Characters to normalize in text preprocessing
TEXT_NORMALIZATION = {
    "lowercase": True,
    "replace_dash": True,          # Replace em-dash and hyphens with space
    "remove_punctuation": True,
    "collapse_whitespace": True,
}


# ============================================================
# VALIDATION
# ============================================================

def validate_settings():
    """
    Validates the settings configuration.
    Raises ValueError if configuration is invalid.
    """

    # Check taxonomy is not empty
    if not TAXONOMY:
        raise ValueError("TAXONOMY cannot be empty")

    # Check all override categories exist in taxonomy
    for cat in HARD_OVERRIDES.keys():
        if cat not in TAXONOMY:
            raise ValueError(f"Hard override category {cat} not found in TAXONOMY")

    # Check override priority categories exist
    for cat in OVERRIDE_PRIORITY:
        if cat not in TAXONOMY:
            raise ValueError(f"Priority category {cat} not found in TAXONOMY")

    # Check confidence thresholds are positive
    for key, val in CONFIDENCE_THRESHOLDS.items():
        if val < 0:
            raise ValueError(f"Confidence threshold {key} must be non-negative")

    return True


# Run validation on import
validate_settings()
