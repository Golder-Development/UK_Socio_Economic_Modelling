"""
Lexicon-Based Classification Engine
====================================

A domain-agnostic, explainable classification system driven by weighted
lexicons and configurable hard override rules.

Usage:
    from classifiers.lexicon_classifier import engine
    from classifiers.lexicon_classifier.manual_overrides_handler import ManualOverridesHandler
    
    # Load your domain-specific settings
    from your_module import settings
    
    # Classify your data
    result = engine.classify_dataframe(df, lexicon_dir, settings)
"""

from .engine import (
    classify_dataframe,
    score_description,
    load_lexicons,
    normalise,
)

from .manual_overrides_handler import (
    ManualOverridesHandler,
    load_and_apply_overrides,
)

__all__ = [
    'classify_dataframe',
    'score_description',
    'load_lexicons',
    'normalise',
    'ManualOverridesHandler',
    'load_and_apply_overrides',
]
