"""
Lexicon-Based Classification Engine
====================================

A domain-agnostic, explainable classification system driven by weighted
lexicons and configurable hard override rules.

Usage:
    from classifiers.lexicon_classifier import engine
    
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

__all__ = [
    'classify_dataframe',
    'score_description',
    'load_lexicons',
    'normalise',
]
