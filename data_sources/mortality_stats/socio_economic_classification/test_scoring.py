"""Test classification scoring logic"""
import sys
sys.path.insert(0, 'H:/VScode/UK_Socio_Economic_Modelling')

from classifiers.lexicon_classifier.engine import load_lexicons, score_description, normalise, matches
from data_sources.mortality_stats.socio_economic_classification import settings
import pandas as pd
import os

test_phrase = "Congenital malformation of heart"
print(f"Testing phrase: '{test_phrase}'")
print("=" * 80)

# Show normalization
normalized = normalise(test_phrase, settings.TEXT_NORMALIZATION)
print(f"\nNormalized text: '{normalized}'")
print("=" * 80)

# Load lexicons
lex_dir = os.path.join(os.path.dirname(__file__), 'lexicons')
lexicons = load_lexicons(lex_dir, settings)

# Score the description
category, scores = score_description(test_phrase, lexicons, settings)

# Show all non-zero scores
print("\n📊 SCORES BY CATEGORY:")
print("-" * 80)
for cat, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
    if score > 0:
        cat_name = settings.TAXONOMY[cat]
        print(f"  {cat} ({cat_name}): {score:.0f}")

# Show winner
print("\n" + "=" * 80)
print(f"🏆 WINNER: {category} ({settings.TAXONOMY[category]}) - Score: {scores[category]:.0f}")
print("=" * 80)

# Detailed token analysis for top categories
print("\n🔍 DETAILED MATCHING ANALYSIS:")
print("=" * 80)

# Get top 3 categories by score
top_cats = sorted([(cat, score) for cat, score in scores.items()], 
                  key=lambda x: x[1], reverse=True)[:3]

for cat, cat_score in top_cats:
    if cat_score == 0:
        continue
    
    print(f"\n{cat} - {settings.TAXONOMY[cat]} (Total: {cat_score:.0f})")
    print("-" * 80)
    
    # Check each term in this category's lexicon
    for term_entry in lexicons[cat]:
        if matches(normalized, term_entry['term'], term_entry['match_type'], settings):
            print(f"  ✓ Matched: '{term_entry['term']}'")
            print(f"    Type: {term_entry['match_type']}, Weight: {term_entry['weight']}")
